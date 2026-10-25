from django.core.management import call_command
from rest_framework.test import APITestCase

from Auditoria.auditoria.models import RegistroAuditoria
from Colaboradores.colaboradores.business import ColaboradorBusiness
from Colaboradores.colaboradores.choices import PERFIL_ATENDENTE, PERFIL_ENTREGADOR
from Colaboradores.colaboradores.management.commands.seed_inicial import SENHA_ADMIN, USERNAME_ADMIN
from Colaboradores.colaboradores.models import User


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
        self.assertIn('access', por_usuario.data)
        self.assertEqual(por_usuario.data['usuario']['perfil'], 'ADMINISTRADOR')

        por_email = self.client.post(
            '/auth/token_jwt/',
            {'username': 'admin@ggas.com.br', 'password': SENHA_ADMIN},
            format='json',
        )
        self.assertEqual(por_email.status_code, 200)
        self.assertEqual(por_email.data['usuario']['username'], USERNAME_ADMIN)

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
                    'password': 'Entrega@123',
                },
            }
        )
        self.assertFalse(entregador.conta.is_active)
        response = self.client.post(
            '/auth/token_jwt/',
            {'username': 'joao', 'password': 'Entrega@123'},
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
                    'password': 'Estoque@123',
                },
            },
            format='json',
        )
        self.assertEqual(criado.status_code, 201)
        self.assertEqual(criado.data['data']['cpf'], '15350946056')
        self.assertEqual(criado.data['data']['conta']['username'], 'carlos')

        for registro in RegistroAuditoria.objects.all():
            self.assertNotIn('Estoque@123', registro.descricao)
            self.assertNotIn('Estoque@123', str(registro.alteracoes))
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
