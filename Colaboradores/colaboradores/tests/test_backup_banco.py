import tempfile
from pathlib import Path

import sqlcipher3
from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase

from ggas.db.sqlite_cifrado.base import _aplicar_chave, copiar_banco_cifrado

SEGREDO = settings.DATABASES['default']['PASSWORD']


class BackupBancoTests(SimpleTestCase):
    def test_copia_cifrada_substitui_o_backup_anterior(self):
        with tempfile.TemporaryDirectory() as pasta:
            origem = Path(pasta) / 'db.sqlite3'
            destino = Path(pasta) / 'db.sqlite3.bak'
            self._gravar(origem, 'primeiro', criar=True)
            destino.write_bytes(b'backup-velho')

            call_command('backup_banco', origem=str(origem), destino=str(destino), verbosity=0)

            self.assertEqual(self._ler(destino), 'primeiro')
            self.assertFalse(Path(str(destino) + '.tmp').exists())
            self._gravar(origem, 'segundo')
            call_command('backup_banco', origem=str(origem), destino=str(destino), verbosity=0)

            self.assertEqual(self._ler(destino), 'segundo')
            self.assertEqual(
                sorted(item.name for item in Path(pasta).iterdir()),
                ['db.sqlite3', 'db.sqlite3.bak'],
            )

    def test_falha_mantem_o_backup_que_ja_existia(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / 'db.sqlite3.bak'
            destino.write_text('backup-velho', encoding='utf-8')
            with self.assertRaises(FileNotFoundError):
                copiar_banco_cifrado(str(Path(pasta) / 'ausente.sqlite3'), str(destino), SEGREDO)
            self.assertEqual(destino.read_text(encoding='utf-8'), 'backup-velho')
            self.assertFalse(Path(str(destino) + '.tmp').exists())

    def _gravar(self, caminho, valor, criar=False):
        conexao = sqlcipher3.connect(str(caminho))
        try:
            _aplicar_chave(conexao, SEGREDO)
            if criar:
                conexao.execute('CREATE TABLE marca (valor TEXT)')
                conexao.execute('INSERT INTO marca (valor) VALUES (?)', (valor,))
            else:
                conexao.execute('UPDATE marca SET valor = ?', (valor,))
            conexao.commit()
        finally:
            conexao.close()

    def _ler(self, caminho):
        conexao = sqlcipher3.connect(str(caminho))
        try:
            _aplicar_chave(conexao, SEGREDO)
            return conexao.execute('SELECT valor FROM marca').fetchone()[0]
        finally:
            conexao.close()
