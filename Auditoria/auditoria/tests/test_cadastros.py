from django.core.management import call_command
from rest_framework.test import APITestCase

from Colaboradores.colaboradores.business import ColaboradorBusiness
from Colaboradores.colaboradores.choices import PERFIL_ATENDENTE, PERFIL_ESTOQUISTA, PERFIL_GERENTE
from Colaboradores.colaboradores.models import User


def criar_colaborador(nome, cpf, perfil, username, email):
    return ColaboradorBusiness().criar(
        {
            'nome': nome,
            'cpf': cpf,
            'telefone': '11999998888',
            'perfil': perfil,
            'ativo': True,
            'conta': {
                'username': username,
                'email': email,
                'password': 'Perfil@123',
            },
        }
    ).conta


class CadastrosEAuditoriaTests(APITestCase):
    def setUp(self):
        call_command('seed_inicial')
        self.admin = User.objects.get(username='admin')
        self.atendente = criar_colaborador(
            'Ana Atendente',
            '39053344705',
            PERFIL_ATENDENTE,
            'ana',
            'ana@ggas.com.br',
        )
        self.estoquista = criar_colaborador(
            'Carlos Estoque',
            '15350946056',
            PERFIL_ESTOQUISTA,
            'carlos',
            'carlos@ggas.com.br',
        )
        self.gerente = criar_colaborador(
            'Marina Gerente',
            '11144477735',
            PERFIL_GERENTE,
            'marina',
            'marina@ggas.com.br',
        )

    def test_atendente_cadastra_cliente_e_so_admin_le_auditoria(self):
        self.client.force_authenticate(self.atendente)
        criado = self.client.post(
            '/clientes/',
            {
                'nome': 'Maria da Silva',
                'telefone': '(11) 98888-7777',
                'logradouro': 'Rua das Flores',
                'numero': '120',
                'bairro': 'Centro',
                'cidade': 'São Paulo',
                'ponto_referencia': 'Em frente à padaria',
            },
            format='json',
        )
        self.assertEqual(criado.status_code, 201)
        self.assertEqual(criado.data['data']['telefone'], '11988887777')
        self.assertEqual(criado.data['data']['total_pedidos'], 0)

        curto = self.client.post(
            '/clientes/',
            {
                'nome': 'Telefone Curto',
                'telefone': '119888877',
                'logradouro': 'Rua das Flores',
                'numero': '120',
                'bairro': 'Centro',
                'cidade': 'São Paulo',
                'ponto_referencia': 'Em frente à padaria',
            },
            format='json',
        )
        self.assertEqual(curto.status_code, 400)

        busca = self.client.get('/clientes/listar/', {'q': '98888'})
        self.assertEqual(busca.status_code, 200)
        self.assertEqual(busca.data['count'], 1)

        self.client.force_authenticate(self.admin)
        auditoria = self.client.get('/auditoria/listar/', {'tipo_entidade': 'CLIENTE'})
        self.assertEqual(auditoria.status_code, 200)
        self.assertEqual(auditoria.data['count'], 1)
        self.assertEqual(auditoria.data['data'][0]['acao'], 'CRIAR_CLIENTE')
        self.assertEqual(auditoria.data['data'][0]['nome_usuario'], 'Ana Atendente')

        self.client.force_authenticate(self.atendente)
        negado = self.client.get('/auditoria/listar/')
        self.assertEqual(negado.status_code, 403)

    def test_atendente_consulta_catalogo_e_nao_grava_produto_nem_fornecedor(self):
        self.client.force_authenticate(self.atendente)
        produto = self.client.post('/produtos/', self._produto(), format='json')
        fornecedor = self.client.post('/fornecedores/', self._fornecedor(), format='json')
        self.assertEqual(produto.status_code, 403)
        self.assertEqual(fornecedor.status_code, 403)

        self.client.force_authenticate(self.estoquista)
        lista = self.client.get('/produtos/listar/')
        self.assertEqual(lista.status_code, 200)

    def test_gerente_cadastra_produto_e_fornecedor_sem_dependencia_entre_eles(self):
        self.client.force_authenticate(self.gerente)
        produto = self.client.post('/produtos/', self._produto(), format='json')
        self.assertEqual(produto.status_code, 201)
        self.assertEqual(produto.data['data']['codigo'], 'GLP-13')
        self.assertEqual(produto.data['data']['saldo_cheio'], 20)

        fornecedor = self.client.post('/fornecedores/', self._fornecedor(), format='json')
        self.assertEqual(fornecedor.status_code, 201)
        self.assertEqual(fornecedor.data['data']['cnpj'], '11222333000181')
        self.assertEqual(fornecedor.data['data']['produtos_fornecidos'], ['GLP 13kg'])

        repetido = self.client.post('/produtos/', self._produto(), format='json')
        self.assertEqual(repetido.status_code, 400)

        invalido = self.client.post(
            '/fornecedores/',
            {**self._fornecedor(), 'cnpj': '11222333000180', 'nome_fantasia': 'Outro'},
            format='json',
        )
        self.assertEqual(invalido.status_code, 400)

    def test_listagem_sem_token_e_atualizacao_fica_na_auditoria(self):
        anonimo = self.client.get('/clientes/listar/')
        self.assertEqual(anonimo.status_code, 401)

        self.client.force_authenticate(self.atendente)
        criado = self.client.post('/clientes/', self._cliente(), format='json')
        cliente_id = criado.data['data']['id']
        atualizado = self.client.patch(
            f'/clientes/{cliente_id}/atualizar/',
            {'ponto_referencia': 'Portão azul'},
            format='json',
        )
        self.assertEqual(atualizado.status_code, 200)
        self.assertEqual(atualizado.data['data']['ponto_referencia'], 'Portão azul')

        self.client.force_authenticate(self.admin)
        auditoria = self.client.get('/auditoria/listar/', {'acao': 'ATUALIZAR_CLIENTE'})
        self.assertEqual(auditoria.data['count'], 1)
        self.assertEqual(
            auditoria.data['data'][0]['alteracoes']['ponto_referencia']['depois'],
            'Portão azul',
        )

    def _cliente(self):
        return {
            'nome': 'José Souza',
            'telefone': '11977776666',
            'logradouro': 'Avenida Brasil',
            'numero': '10',
            'bairro': 'Jardins',
            'cidade': 'São Paulo',
            'ponto_referencia': 'Esquina do mercado',
        }

    def _produto(self):
        return {
            'codigo': 'glp-13',
            'nome': 'GLP 13kg Botijão Azul',
            'marca': 'Ultragaz',
            'categoria': 'GAS',
            'preco_venda': '115.00',
            'preco_custo': '85.00',
            'saldo_cheio': 20,
            'saldo_seco': 0,
            'estoque_minimo': 10,
            'unidade': 'Botijão P13',
        }

    def _fornecedor(self):
        return {
            'nome_fantasia': 'Ultragaz',
            'razao_social': 'Companhia Ultragaz S.A.',
            'cnpj': '11.222.333/0001-81',
            'telefone': '1133334444',
            'nome_contato': 'Paulo Compras',
            'endereco': 'Avenida Paulista, 1000',
            'cidade': 'São Paulo',
            'produtos_fornecidos': ['GLP 13kg'],
        }
