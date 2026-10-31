import datetime
import decimal
import hashlib
import sqlite3
import threading
from pathlib import Path

import sqlcipher3
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.sqlite3.base import (
    FORMAT_QMARK_REGEX,
    DatabaseWrapper as SQLiteDatabaseWrapper,
    adapt_date,
    adapt_datetime,
    decoder,
)
from django.utils.asyncio import async_unsafe
from django.utils.dateparse import parse_date, parse_datetime, parse_time
from django.db.backends.sqlite3._functions import register as register_functions

_cadeado = threading.Lock()

sqlcipher3.register_converter('bool', b'1'.__eq__)
sqlcipher3.register_converter('date', decoder(parse_date))
sqlcipher3.register_converter('time', decoder(parse_time))
sqlcipher3.register_converter('datetime', decoder(parse_datetime))
sqlcipher3.register_converter('timestamp', decoder(parse_datetime))
sqlcipher3.register_adapter(decimal.Decimal, str)
sqlcipher3.register_adapter(datetime.date, adapt_date)
sqlcipher3.register_adapter(datetime.datetime, adapt_datetime)


def _chave_hex(segredo: str) -> str:
    return hashlib.sha256(segredo.encode()).hexdigest()


def _aplicar_chave(conexao, segredo: str) -> None:
    conexao.execute(f"PRAGMA key = \"x'{_chave_hex(segredo)}'\"")


def _banco_claro(caminho: str) -> bool:
    if not caminho or caminho == ':memory:' or caminho.startswith('file:'):
        return False
    arquivo = Path(caminho)
    if not arquivo.exists() or arquivo.stat().st_size < 16:
        return False
    with arquivo.open('rb') as handle:
        return handle.read(16) == b'SQLite format 3\x00'


def _migrar_banco_claro(caminho: str, segredo: str) -> None:
    with _cadeado:
        if not _banco_claro(caminho):
            return
        origem = sqlite3.connect(caminho)
        try:
            origem.execute('PRAGMA wal_checkpoint(FULL)')
            origem.execute('PRAGMA foreign_keys = OFF')
            script = '\n'.join(origem.iterdump())
        finally:
            origem.close()

        reserva = Path(caminho + '.claro.bak')
        if reserva.exists():
            reserva.unlink()
        Path(caminho).replace(reserva)
        for extra in (caminho + '-wal', caminho + '-shm', caminho + '-journal'):
            sobra = Path(extra)
            if sobra.exists():
                sobra.unlink()

        destino = sqlcipher3.connect(caminho)
        try:
            _aplicar_chave(destino, segredo)
            destino.execute('PRAGMA foreign_keys = OFF')
            destino.executescript(script)
            destino.commit()
        finally:
            destino.close()


class CursorCifrado(sqlcipher3.Cursor):
    def execute(self, query, params=None):
        if params is None:
            return super().execute(query)
        nomes = list(params) if isinstance(params, dict) else None
        return super().execute(self._converter(query, nomes), params)

    def executemany(self, query, param_list):
        return super().executemany(self._converter(query, None), param_list)

    def _converter(self, query, nomes):
        if nomes is None:
            return FORMAT_QMARK_REGEX.sub('?', query).replace('%%', '%')
        return query % {nome: f':{nome}' for nome in nomes}


class DatabaseWrapper(SQLiteDatabaseWrapper):
    Database = sqlcipher3

    @async_unsafe
    def get_new_connection(self, conn_params):
        segredo = self.settings_dict.get('PASSWORD') or ''
        if not segredo:
            raise ImproperlyConfigured('Defina DJANGO_DB_KEY para abrir o banco cifrado.')

        params = dict(conn_params)
        params.pop('transaction_mode', None)
        banco = params.get('database')
        if banco not in (None, ':memory:'):
            params['database'] = str(banco)
            _migrar_banco_claro(params['database'], segredo)

        conexao = sqlcipher3.connect(**params)
        _aplicar_chave(conexao, segredo)
        register_functions(conexao)
        conexao.execute('PRAGMA foreign_keys = ON')
        conexao.execute('PRAGMA legacy_alter_table = OFF')
        return conexao

    def create_cursor(self, name=None):
        return self.connection.cursor(factory=CursorCifrado)
