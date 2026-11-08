from datetime import timedelta

from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory, override_settings
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from Auditoria.auditoria.models import RegistroAuditoria
from Auth.auth.models import Sessao
from Auth.auth.rede import ip_do_cliente
from Colaboradores.colaboradores.business import ColaboradorBusiness
from Colaboradores.colaboradores.choices import PERFIL_ATENDENTE, PERFIL_ENTREGADOR, PERFIL_GERENTE
from Colaboradores.colaboradores.management.commands.seed_inicial import (
    SENHA_ADMIN,
    USERNAME_ADMIN,
    deve_criar_administrador,
    texto_criacao,
)
from Colaboradores.colaboradores.models import User
from ggas.segredos import (
    CHAVE_BANCO_EXEMPLO,
    CHAVE_SECRETA_EXEMPLO,
    CHAVE_SECRETA_PADRAO,
    recusar_segredo_publico,
)


class AcessoInicialTests(APITestCase):
    def setUp(self):
        call_command('seed_inicial')
        self.admin = User.objects.get(username=USERNAME_ADMIN)
        self.atendente = ColaboradorBusiness().criar(
            {
                'nome': 'Ana Atendente',
                'cpf': '39053344705',
                'telefone': '11988887777',
                'perfil': PERFIL_ATENDENTE,
                'ativo': True,
                'conta': {
                    'username': 'ana',
                    'email': 'ana@ggas.com.br',
                    'password': 'Atendente@123',
                },
            }
        )

    def test_health_usa_sqlite(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['banco'], 'sqlite')

    def test_login_por_usuario_e_por_email(self):
        por_usuario = self.client.post(
            '/auth/token_jwt/',
            {'username': USERNAME_ADMIN, 'password': SENHA_ADMIN},
            format='json',
        )
        self.assertEqual(por_usuario.status_code, 200)
        self.assertNotIn('access', por_usuario.data)
        self.assertNotIn('refresh', por_usuario.data)
        self.assertTrue(por_usuario.cookies['ggas_sessao']['httponly'])
        self.assertEqual(por_usuario.cookies['ggas_sessao']['samesite'], 'Lax')
        self.assertEqual(por_usuario.data['usuario']['perfil'], 'ADMINISTRADOR')
        sessao = self.client.get('/auth/eu/')
        self.assertEqual(sessao.status_code, 200)

        por_email = self.client.post(
            '/auth/token_jwt/',
            {'username': 'admin@ggas.com.br', 'password': SENHA_ADMIN},
            format='json',
        )
        self.assertEqual(por_email.status_code, 200)
        self.assertEqual(por_email.data['usuario']['username'], USERNAME_ADMIN)

    def test_logout_revoga_a_sessao_na_hora(self):
        entrada = self.client.post(
            '/auth/token_jwt/',
            {'username': USERNAME_ADMIN, 'password': SENHA_ADMIN},
            format='json',
        )
        self.assertEqual(entrada.status_code, 200)
        self.assertEqual(self.client.get('/auth/eu/').status_code, 200)
        saida = self.client.post('/auth/sair/')
        self.assertEqual(saida.status_code, 200)
        self.assertEqual(self.client.get('/auth/eu/').status_code, 401)

    def test_colaborador_inativo_nao_entra(self):
        entregador = ColaboradorBusiness().criar(
            {
                'nome': 'João Entregas',
                'cpf': '11144477735',
                'telefone': '11977776666',
                'perfil': PERFIL_ENTREGADOR,
                'ativo': False,
                'placa_veiculo': 'ABC1D23',
                'conta': {
                    'username': 'joao',
                    'email': 'joao@ggas.com.br',
                    'password': 'Entrega@12345',
                },
            }
        )
        self.assertFalse(entregador.conta.is_active)
        response = self.client.post(
            '/auth/token_jwt/',
            {'username': 'joao', 'password': 'Entrega@12345'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

        self.client.force_authenticate(self.admin)
        desligado = self.client.patch(
            f'/colaboradores/{self.atendente.id}/atualizar/',
            {'ativo': False},
            format='json',
        )
        self.assertEqual(desligado.status_code, 200, desligado.data)
        self.client.force_authenticate(user=None)
        conta_inativa = self.client.post(
            '/auth/token_jwt/',
            {'username': 'ana', 'password': 'Atendente@123'},
            format='json',
        )
        self.assertEqual(conta_inativa.status_code, 400)

    def test_sessao_e_listagem_exigem_token(self):
        anonimo = self.client.get('/colaboradores/listar/')
        self.assertEqual(anonimo.status_code, 401)

        self.client.force_authenticate(self.admin)
        sessao = self.client.get('/auth/eu/')
        self.assertEqual(sessao.status_code, 200)
        self.assertEqual(sessao.data['data']['username'], USERNAME_ADMIN)

        lista = self.client.get('/colaboradores/listar/', {'perfil': 'ENTREGADOR'})
        self.assertEqual(lista.status_code, 200)
        self.assertEqual(lista.data['count'], 0)

    def test_atendente_nao_cadastra_colaborador_e_admin_cadastra(self):
        self.client.force_authenticate(self.atendente.conta)
        negado = self.client.post(
            '/colaboradores/',
            {
                'nome': 'Carlos Estoque',
                'cpf': '15350946056',
                'telefone': '11966665555',
                'perfil': 'ESTOQUISTA',
            },
            format='json',
        )
        self.assertEqual(negado.status_code, 403)

        self.client.force_authenticate(self.admin)
        criado = self.client.post(
            '/colaboradores/',
            {
                'nome': 'Carlos Estoque',
                'cpf': '153.509.460-56',
                'telefone': '11966665555',
                'perfil': 'ESTOQUISTA',
                'conta': {
                    'username': 'carlos',
                    'email': 'carlos@ggas.com.br',
                    'password': 'Estoque@1234',
                },
            },
            format='json',
        )
        self.assertEqual(criado.status_code, 201)
        self.assertEqual(criado.data['data']['cpf'], '15350946056')
        self.assertEqual(criado.data['data']['conta']['username'], 'carlos')

        for registro in RegistroAuditoria.objects.all():
            self.assertNotIn('Estoque@1234', registro.descricao)
            self.assertNotIn('Estoque@1234', str(registro.alteracoes))
            self.assertNotIn('password', registro.alteracoes)
        self.assertFalse(any(campo.name == 'password' for campo in User.history.model._meta.fields))

        curto = self.client.post(
            '/colaboradores/',
            {
                'nome': 'Telefone Curto',
                'cpf': '11144477735',
                'telefone': '1234567',
                'perfil': 'ENTREGADOR',
            },
            format='json',
        )
        self.assertEqual(curto.status_code, 400)
        oito = self.client.post(
            '/colaboradores/',
            {
                'nome': 'Oito Digitos',
                'cpf': '12345678909',
                'telefone': '12345678',
                'perfil': 'ENTREGADOR',
            },
            format='json',
        )
        self.assertEqual(oito.status_code, 201, oito.data)
        self.assertEqual(oito.data['data']['telefone'], '12345678')

    def test_nao_inativa_o_ultimo_administrador(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f'/colaboradores/{self.admin.colaborador_id}/atualizar/',
            {'ativo': False},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('administrador', response.data['detail'].lower())

        perfil = self.client.patch(
            f'/colaboradores/{self.admin.colaborador_id}/atualizar/',
            {'perfil': 'GERENTE'},
            format='json',
        )
        self.assertEqual(perfil.status_code, 400)
        self.admin.colaborador.refresh_from_db()
        self.assertEqual(self.admin.colaborador.perfil, 'ADMINISTRADOR')
        self.assertTrue(self.admin.colaborador.ativo)

    def test_desativar_colaborador_revoga_a_sessao(self):
        operador = APIClient()
        entrada = operador.post(
            '/auth/token_jwt/',
            {'username': 'ana', 'password': 'Atendente@123'},
            format='json',
        )
        self.assertEqual(entrada.status_code, 200)
        self.assertEqual(operador.get('/auth/eu/').status_code, 200)

        self.client.force_authenticate(self.admin)
        desligado = self.client.patch(
            f'/colaboradores/{self.atendente.id}/atualizar/',
            {'ativo': False},
            format='json',
        )
        self.assertEqual(desligado.status_code, 200, desligado.data)
        self.assertEqual(operador.get('/auth/eu/').status_code, 401)

    def test_gerente_nao_altera_administrador_nem_outro_gerente(self):
        gerente = ColaboradorBusiness().criar(
            {
                'nome': 'Gisela Gerente',
                'cpf': '86288366757',
                'telefone': '11955554444',
                'perfil': PERFIL_GERENTE,
                'ativo': True,
                'conta': {
                    'username': 'gisela',
                    'email': 'gisela@ggas.com.br',
                    'password': 'Gestao@123456',
                },
            }
        )
        self.client.force_authenticate(gerente.conta)

        proprio = self.client.patch(
            f'/colaboradores/{gerente.id}/atualizar/',
            {'perfil': 'ADMINISTRADOR'},
            format='json',
        )
        self.assertEqual(proprio.status_code, 403)
        gerente.refresh_from_db()
        self.assertEqual(gerente.perfil, PERFIL_GERENTE)

        novo_admin = self.client.post(
            '/colaboradores/',
            {
                'nome': 'Outro Admin',
                'cpf': '15350946056',
                'telefone': '11944443333',
                'perfil': 'ADMINISTRADOR',
            },
            format='json',
        )
        self.assertEqual(novo_admin.status_code, 403)
        self.assertFalse(User.objects.filter(username='outro').exists())

        outro_gerente = self.client.post(
            '/colaboradores/',
            {
                'nome': 'Outro Gerente',
                'cpf': '12345678909',
                'telefone': '11933332222',
                'perfil': 'GERENTE',
            },
            format='json',
        )
        self.assertEqual(outro_gerente.status_code, 403)

        senha = self.client.patch(
            f'/colaboradores/{self.admin.colaborador_id}/conta/atualizar/',
            {'password': 'Invadiu@2026'},
            format='json',
        )
        self.assertEqual(senha.status_code, 403)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password(SENHA_ADMIN))

        entregador = self.client.post(
            '/colaboradores/',
            {
                'nome': 'João Entregas',
                'cpf': '11144477735',
                'telefone': '11977776666',
                'perfil': 'ENTREGADOR',
                'placa_veiculo': 'ABC1D23',
            },
            format='json',
        )
        self.assertEqual(entregador.status_code, 201, entregador.data)
        entregador_id = entregador.data['data']['id']
        editado = self.client.patch(
            f'/colaboradores/{entregador_id}/atualizar/',
            {'telefone': '11912345678'},
            format='json',
        )
        self.assertEqual(editado.status_code, 200, editado.data)
        self.assertEqual(editado.data['data']['perfil'], 'ENTREGADOR')

        administrador = ColaboradorBusiness().criar(
            {
                'nome': 'Bruno Admin',
                'cpf': '45317828791',
                'telefone': '11922221111',
                'perfil': 'ADMINISTRADOR',
                'ativo': True,
                'conta': {
                    'username': 'bruno',
                    'email': 'bruno@ggas.com.br',
                    'password': 'BrunoAcesso@2026',
                },
            }
        )
        self.assertFalse(administrador.conta.is_superuser)
        self.client.force_authenticate(administrador.conta)
        promovido = self.client.patch(
            f'/colaboradores/{entregador_id}/atualizar/',
            {'perfil': 'GERENTE'},
            format='json',
        )
        self.assertEqual(promovido.status_code, 200, promovido.data)
        self.assertEqual(promovido.data['data']['perfil'], 'GERENTE')
        nova_senha = self.client.patch(
            f'/colaboradores/{self.admin.colaborador_id}/conta/atualizar/',
            {'password': 'CofreNovo@2026'},
            format='json',
        )
        self.assertEqual(nova_senha.status_code, 200, nova_senha.data)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('CofreNovo@2026'))

    def test_schema_exige_administrador_e_a_saude_continua_publica(self):
        self.assertEqual(self.client.get('/api/health/').status_code, 200)
        self.assertEqual(self.client.get('/api/schema/').status_code, 401)
        self.client.force_authenticate(self.atendente.conta)
        for caminho in ('/api/schema/', '/api/schema/swagger/', '/api/schema/redoc/'):
            resposta = self.client.get(caminho)
            self.assertEqual(resposta.status_code, 403, caminho)
        self.admin.is_superuser = False
        self.admin.is_staff = False
        self.admin.save(update_fields=['is_superuser', 'is_staff'])
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get('/api/schema/').status_code, 200)

    def test_segredo_publico_e_seed_ficam_fora_do_ambiente_publicado(self):
        with self.assertRaises(ImproperlyConfigured):
            recusar_segredo_publico(False, False, CHAVE_SECRETA_PADRAO, 'chave-real-do-banco')
        with self.assertRaises(ImproperlyConfigured):
            recusar_segredo_publico(False, False, CHAVE_SECRETA_EXEMPLO, 'chave-real-do-banco')
        with self.assertRaises(ImproperlyConfigured):
            recusar_segredo_publico(False, False, 'chave-real-da-sessao', '')
        with self.assertRaises(ImproperlyConfigured):
            recusar_segredo_publico(False, False, 'chave-real-da-sessao', CHAVE_BANCO_EXEMPLO)
        recusar_segredo_publico(True, False, CHAVE_SECRETA_PADRAO, CHAVE_BANCO_EXEMPLO)
        recusar_segredo_publico(False, True, CHAVE_SECRETA_PADRAO, '')
        recusar_segredo_publico(False, False, 'chave-real-da-sessao', 'chave-real-do-banco')

        self.assertFalse(deve_criar_administrador(False, False))
        self.assertTrue(deve_criar_administrador(True, False))
        self.assertTrue(deve_criar_administrador(False, True))
        self.assertNotIn('Senha:', texto_criacao(False))
        self.assertIn(SENHA_ADMIN, texto_criacao(True))

    def test_ip_de_proxy_usa_o_ultimo_salto_e_ignora_o_cliente_fora_dele(self):
        pedido = RequestFactory().get(
            '/',
            REMOTE_ADDR='127.0.0.1',
            HTTP_X_FORWARDED_FOR='1.2.3.4, 9.9.9.9',
        )
        self.assertEqual(ip_do_cliente(pedido), '127.0.0.1')
        with override_settings(IP_CABECALHO_PROXY='HTTP_X_FORWARDED_FOR'):
            self.assertEqual(ip_do_cliente(pedido), '9.9.9.9')

    def test_login_audita_acerto_recusa_e_bloqueio_sem_a_senha(self):
        aceito = self.client.post(
            '/auth/token_jwt/',
            {'username': USERNAME_ADMIN, 'password': SENHA_ADMIN},
            format='json',
        )
        self.assertEqual(aceito.status_code, 200, aceito.data)
        registro = RegistroAuditoria.objects.get(acao='LOGIN_ACEITO')
        self.assertEqual(registro.usuario_id, self.admin.id)
        self.assertEqual(registro.alteracoes['ip'], '127.0.0.1')
        self.assertNotIn(SENHA_ADMIN, registro.descricao)
        self.assertNotIn('password', registro.alteracoes)

        self.client.post('/auth/sair/')
        senha_errada = 'senha-errada-demais'
        for indice in range(5):
            recusa = self.client.post(
                '/auth/token_jwt/',
                {'username': USERNAME_ADMIN, 'password': senha_errada},
                format='json',
                HTTP_X_FORWARDED_FOR=f'10.0.0.{indice}',
            )
            self.assertEqual(recusa.status_code, 400, recusa.data)
        bloqueado = self.client.post(
            '/auth/token_jwt/',
            {'username': USERNAME_ADMIN, 'password': senha_errada},
            format='json',
            HTTP_X_FORWARDED_FOR='10.9.9.9',
        )
        self.assertEqual(bloqueado.status_code, 429, bloqueado.data)
        self.assertTrue(RegistroAuditoria.objects.filter(acao='LOGIN_RECUSADO', usuario=self.admin).exists())
        self.assertTrue(RegistroAuditoria.objects.filter(acao='LOGIN_BLOQUEADO', usuario=self.admin).exists())
        for registro in RegistroAuditoria.objects.filter(acao__startswith='LOGIN_'):
            self.assertNotIn(senha_errada, registro.descricao)
            self.assertNotIn(senha_errada, str(registro.alteracoes))
            self.assertNotIn('password', registro.alteracoes)

        desconhecido = APIClient()
        resposta = desconhecido.post(
            '/auth/token_jwt/',
            {'username': 'ninguem', 'password': senha_errada},
            format='json',
        )
        self.assertEqual(resposta.status_code, 400)
        sem_conta = RegistroAuditoria.objects.get(acao='LOGIN_RECUSADO', entidade_id='ninguem')
        self.assertIsNone(sem_conta.usuario_id)
        self.assertEqual(sem_conta.nome_usuario, 'ninguem')

    def test_senha_nova_curta_e_recusada_e_a_troca_guarda_o_ip(self):
        self.client.force_authenticate(self.admin)
        curta = self.client.patch(
            f'/colaboradores/{self.atendente.id}/conta/atualizar/',
            {'password': 'Abcdef@1234'},
            format='json',
        )
        self.assertEqual(curta.status_code, 400, curta.data)
        nova = 'ContaNova@2026'
        troca = self.client.patch(
            f'/colaboradores/{self.atendente.id}/conta/atualizar/',
            {'password': nova},
            format='json',
        )
        self.assertEqual(troca.status_code, 200, troca.data)
        registro = RegistroAuditoria.objects.get(acao='SENHA_ALTERADA')
        self.assertEqual(registro.alteracoes['ip'], '127.0.0.1')
        self.assertTrue(registro.alteracoes['senha_alterada'])
        self.assertNotIn(nova, registro.descricao)
        self.assertNotIn(nova, str(registro.alteracoes))


class SessaoCookieTests(APITestCase):
    def setUp(self):
        call_command('seed_inicial')
        self.admin = User.objects.get(username=USERNAME_ADMIN)
        self.client = APIClient(enforce_csrf_checks=True)

    def _token(self):
        return self.client.cookies['csrftoken'].value

    def _entrar(self):
        preparado = self.client.get('/auth/csrf/')
        self.assertEqual(preparado.status_code, 200)
        self.assertFalse(preparado.cookies['csrftoken']['httponly'])
        self.assertEqual(preparado.cookies['csrftoken']['samesite'], 'Lax')
        return self.client.post(
            '/auth/token_jwt/',
            {'username': USERNAME_ADMIN, 'password': SENHA_ADMIN},
            format='json',
            HTTP_X_CSRFTOKEN=self._token(),
        )

    def test_mutacao_sem_csrf_e_recusada_e_com_csrf_segue(self):
        sem_token = self.client.post(
            '/auth/token_jwt/',
            {'username': USERNAME_ADMIN, 'password': SENHA_ADMIN},
            format='json',
        )
        self.assertEqual(sem_token.status_code, 403)

        entrada = self._entrar()
        self.assertEqual(entrada.status_code, 200, entrada.data)
        sem_cabecalho = self.client.patch(
            f'/colaboradores/{self.admin.colaborador_id}/atualizar/',
            {'telefone': '11999998888'},
            format='json',
        )
        self.assertEqual(sem_cabecalho.status_code, 403)
        self.assertIn('CSRF', str(sem_cabecalho.data['detail']))

        com_cabecalho = self.client.patch(
            f'/colaboradores/{self.admin.colaborador_id}/atualizar/',
            {'telefone': '11999998888'},
            format='json',
            HTTP_X_CSRFTOKEN=self._token(),
        )
        self.assertEqual(com_cabecalho.status_code, 200, com_cabecalho.data)

        saida_sem = self.client.post('/auth/sair/')
        self.assertEqual(saida_sem.status_code, 403)
        saida = self.client.post('/auth/sair/', HTTP_X_CSRFTOKEN=self._token())
        self.assertEqual(saida.status_code, 200)
        self.assertEqual(self.client.get('/auth/eu/').status_code, 401)

    def test_troca_de_senha_revoga_a_sessao(self):
        entrada = self._entrar()
        self.assertEqual(entrada.status_code, 200, entrada.data)
        troca = self.client.patch(
            f'/colaboradores/{self.admin.colaborador_id}/conta/atualizar/',
            {'password': 'ContaNova@2026'},
            format='json',
            HTTP_X_CSRFTOKEN=self._token(),
        )
        self.assertEqual(troca.status_code, 200, troca.data)
        self.assertEqual(self.client.get('/auth/eu/').status_code, 401)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('ContaNova@2026'))

    def test_sessao_ociosa_expira_e_o_uso_recente_permanece(self):
        entrada = self._entrar()
        self.assertEqual(entrada.status_code, 200, entrada.data)
        sessao = Sessao.objects.get(usuario=self.admin)

        sessao.ultimo_acesso = timezone.now() - timedelta(seconds=30)
        sessao.save(update_fields=['ultimo_acesso'])
        self.assertEqual(self.client.get('/auth/eu/').status_code, 200)
        sessao.refresh_from_db()
        acesso_recente = sessao.ultimo_acesso

        sessao.ultimo_acesso = timezone.now() - timedelta(minutes=2)
        sessao.save(update_fields=['ultimo_acesso'])
        self.assertEqual(self.client.get('/auth/eu/').status_code, 200)
        sessao.refresh_from_db()
        self.assertGreater(sessao.ultimo_acesso, acesso_recente)

        sessao.ultimo_acesso = timezone.now() - timedelta(minutes=31)
        sessao.save(update_fields=['ultimo_acesso'])
        self.assertEqual(self.client.get('/auth/eu/').status_code, 401)
