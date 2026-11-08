import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import sqlcipher3
from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase

from ggas.backup_automatico import INTERVALO_SEGUNDOS, copiar_se_vencido, vencido
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

    def test_backup_recente_nao_dispara_outra_copia(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / 'db.sqlite3.bak'
            agora = time.time()
            self.assertTrue(vencido(destino, agora=agora))
            destino.write_bytes(b'recente')
            self.assertFalse(vencido(destino, agora=agora + 60))
            os.utime(destino, (agora - INTERVALO_SEGUNDOS, agora - INTERVALO_SEGUNDOS))
            self.assertTrue(vencido(destino, agora=agora))

            with patch('ggas.backup_automatico.caminho_padrao', return_value=destino), patch(
                'ggas.backup_automatico.vencido', return_value=False
            ), patch('ggas.backup_automatico.executar') as copia:
                self.assertFalse(copiar_se_vencido())
            copia.assert_not_called()

    def test_backup_vencido_dispara_a_copia(self):
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / 'db.sqlite3.bak'
            destino.write_bytes(b'velho')
            with patch('ggas.backup_automatico.caminho_padrao', return_value=destino), patch(
                'ggas.backup_automatico.vencido', return_value=True
            ), patch('ggas.backup_automatico.executar', return_value=str(destino)) as copia:
                self.assertTrue(copiar_se_vencido())
            copia.assert_called_once_with(destino=str(destino))

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
