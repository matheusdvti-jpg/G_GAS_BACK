import logging
import os
import sys
import threading
import time
from pathlib import Path

from django.conf import settings

from ggas.db.sqlite_cifrado.base import copiar_banco_cifrado

logger = logging.getLogger('ggas')

INTERVALO_SEGUNDOS = 7 * 24 * 60 * 60
ESPERA_ENTRE_CHECAGENS = 60 * 60
_espera_inicial = 15
_thread = None


def caminho_padrao() -> Path:
    return Path(settings.BASE_DIR) / 'backups' / 'db.sqlite3.bak'


def vencido(destino: Path, intervalo: float = INTERVALO_SEGUNDOS, agora: float | None = None) -> bool:
    if not destino.is_file():
        return True
    momento = time.time() if agora is None else agora
    return momento - destino.stat().st_mtime >= intervalo


def executar(origem: str = '', destino: str = '') -> str:
    config = settings.DATABASES['default']
    arquivo_origem = origem or str(config.get('NAME') or '')
    segredo = config.get('PASSWORD') or ''
    arquivo_destino = destino or str(caminho_padrao())
    copiar_banco_cifrado(arquivo_origem, arquivo_destino, segredo)
    return arquivo_destino


def copiar_se_vencido() -> bool:
    destino = caminho_padrao()
    if not vencido(destino):
        return False
    with _trava() as reservado:
        if not reservado or not vencido(destino):
            return False
        executar(destino=str(destino))
    return True


def iniciar() -> None:
    global _thread
    if settings.DEBUG or 'test' in sys.argv:
        return
    if _thread is not None and _thread.is_alive():
        return
    _thread = threading.Thread(target=_ciclo, name='backup-banco', daemon=True)
    _thread.start()
    logger.info('Backup semanal ligado. Arquivo: %s', caminho_padrao())


def _ciclo() -> None:
    time.sleep(_espera_inicial)
    while True:
        try:
            if copiar_se_vencido():
                logger.info('Backup automático gravado em %s.', caminho_padrao())
        except Exception:
            logger.exception(
                'Backup automático não foi concluído. A cópia anterior foi mantida.'
            )
        time.sleep(ESPERA_ENTRE_CHECAGENS)


class _Trava:
    def __init__(self):
        self._arquivo = None
        self.reservado = False

    def __enter__(self):
        if os.name == 'nt':
            self.reservado = True
            return self.reservado
        import fcntl

        pasta = caminho_padrao().parent
        pasta.mkdir(parents=True, exist_ok=True)
        self._arquivo = open(pasta / '.backup.lock', 'a', encoding='utf-8')
        try:
            fcntl.flock(self._arquivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._arquivo.close()
            self._arquivo = None
            self.reservado = False
            return self.reservado
        self.reservado = True
        return self.reservado

    def __exit__(self, *args):
        if self._arquivo is None:
            return
        import fcntl

        fcntl.flock(self._arquivo.fileno(), fcntl.LOCK_UN)
        self._arquivo.close()
        self._arquivo = None


def _trava():
    return _Trava()
