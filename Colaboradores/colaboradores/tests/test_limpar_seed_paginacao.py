from django.core.management import call_command
from rest_framework.test import APITestCase

from Auditoria.auditoria.models import RegistroAuditoria
from Catalogo.fornecedores.models import Fornecedor
from Catalogo.produtos.business import ProdutoBusiness
from Catalogo.produtos.models import Produto
from Clientes.clientes.business import ClienteBusiness
from Clientes.clientes.models import Cliente
from Colaboradores.colaboradores.management.commands.seed_inicial import CPF_ADMIN, SENHA_ADMIN, USERNAME_ADMIN
from Colaboradores.colaboradores.management.commands.seed_paginacao import (
    CLIENTES,
    PRODUTOS_ACESSORIO,
    PRODUTOS_AGUA,
    PRODUTOS_GAS,
)
from Colaboradores.colaboradores.models import Colaborador, User
from Estoque.estoque.models import MovimentacaoEstoque
from Pedidos.pedidos.business import PedidoBusiness
from Pedidos.pedidos.choices import PAGAMENTO_PIX
from Pedidos.pedidos.models import ItemPedido, Pedido


class LimparSeedPaginacaoTests(APITestCase):
    def setUp(self):
        call_command('seed_paginacao', verbosity=0)
        self.admin = User.objects.get(username=USERNAME_ADMIN)

    def test_sem_confirmar_nao_apaga(self):
        produtos = PRODUTOS_GAS + PRODUTOS_AGUA + PRODUTOS_ACESSORIO
        call_command('limpar_seed_paginacao', verbosity=0)
        self.assertEqual(Produto.objects.count(), produtos)
        self.assertEqual(Cliente.objects.count(), CLIENTES)
        self.assertEqual(User.objects.filter(username=USERNAME_ADMIN).count(), 1)

    def test_confirmado_remove_o_seed_e_preserva_o_admin_e_o_cadastro_real(self):
        cliente = ClienteBusiness().criar(
            {
                'nome': 'Cliente Real da Loja',
                'telefone': '11888887777',
                'telefone_secundario': '',
                'logradouro': 'Rua do Comércio',
                'numero': '10',
                'complemento': '',
                'bairro': 'Centro',
                'cidade': 'São Paulo',
                'ponto_referencia': '',
                'observacoes': 'Cliente atendido no balcão',
            },
            self.admin,
        )
        call_command('limpar_seed_paginacao', confirmar=True, verbosity=0)

        self.assertEqual(Produto.objects.count(), 0)
        self.assertEqual(Fornecedor.objects.count(), 0)
        self.assertEqual(Pedido.objects.count(), 0)
        self.assertEqual(ItemPedido.objects.count(), 0)
        self.assertEqual(MovimentacaoEstoque.objects.count(), 0)
        self.assertEqual(Cliente.objects.count(), 1)
        self.assertEqual(Cliente.objects.get().nome, cliente.nome)
        self.assertEqual(Colaborador.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)

        admin = User.objects.get(username=USERNAME_ADMIN)
        self.assertEqual(admin.email, 'admin@ggas.com.br')
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.check_password(SENHA_ADMIN))
        self.assertEqual(admin.colaborador.nome, 'Administrador')
        self.assertEqual(admin.colaborador.cpf, CPF_ADMIN)
        self.assertEqual(Colaborador.objects.filter(perfil='ENTREGADOR').count(), 0)

        self.assertFalse(Produto.history.filter(codigo='PG-01').exists())
        self.assertFalse(Cliente.history.filter(nome='Cliente Paginação 01').exists())
        self.assertTrue(Cliente.history.filter(id=cliente.id).exists())
        self.assertTrue(User.history.filter(username=USERNAME_ADMIN).exists())
        self.assertEqual(RegistroAuditoria.objects.count(), 1)
        self.assertIn('Cliente Real da Loja', RegistroAuditoria.objects.get().descricao)

    def test_apaga_ficha_editada_e_pedido_feito_em_cima_do_seed(self):
        produto = Produto.objects.get(codigo='PG-01')
        produto.nome = 'Botijão alterado no teste'
        produto.descricao = 'Ficha mexida'
        produto.save(update_fields=['nome', 'descricao', 'updated_at'])
        ficha = Cliente.objects.get(nome='Cliente Paginação 02')
        ficha.nome = 'Maria Teste'
        ficha.observacoes = 'alterei a observação'
        ficha.save(update_fields=['nome', 'observacoes', 'updated_at'])
        cliente = self._cliente_real()
        entregador = Colaborador.objects.get(nome='Entregador Paginação 01')
        PedidoBusiness().criar(
            {
                'cliente_id': cliente.id,
                'entregador_id': entregador.id,
                'forma_pagamento': PAGAMENTO_PIX,
                'itens': [{'produto_id': produto.id, 'quantidade': 1}],
                'observacoes': 'Pedido de teste',
            },
            self.admin,
        )

        call_command('limpar_seed_paginacao', confirmar=True, verbosity=0)

        self.assertFalse(Produto.objects.filter(codigo='PG-01').exists())
        self.assertFalse(Cliente.objects.filter(nome='Maria Teste').exists())
        self.assertFalse(Pedido.objects.filter(observacoes='Pedido de teste').exists())
        self.assertEqual(Pedido.objects.count(), 0)
        restante = Cliente.objects.get()
        self.assertEqual(restante.nome, 'Cliente Real da Loja')
        self.assertEqual(restante.total_pedidos, 0)
        self.assertEqual(str(restante.total_gasto), '0.00')
        self.assertTrue(User.objects.filter(username=USERNAME_ADMIN).exists())

    def test_repoe_saldo_de_produto_que_nao_e_do_seed(self):
        produto = ProdutoBusiness().criar(
            {
                'codigo': 'REAL-01',
                'nome': 'Botijão da loja',
                'descricao': 'Produto de verdade',
                'marca': 'Nacional',
                'categoria': 'GAS',
                'preco_venda': '120.00',
                'preco_custo': '80.00',
                'saldo_cheio': 10,
                'saldo_seco': 0,
                'estoque_minimo': 2,
                'unidade': 'un',
                'ativo': True,
            },
            self.admin,
        )
        cliente = self._cliente_real()
        entregador = Colaborador.objects.get(nome='Entregador Paginação 01')
        PedidoBusiness().criar(
            {
                'cliente_id': cliente.id,
                'entregador_id': entregador.id,
                'forma_pagamento': PAGAMENTO_PIX,
                'itens': [{'produto_id': produto.id, 'quantidade': 1}],
                'observacoes': 'Venda de teste com entregador do seed',
            },
            self.admin,
        )
        self.assertEqual(Produto.objects.get(codigo='REAL-01').saldo_cheio, 9)

        call_command('limpar_seed_paginacao', confirmar=True, verbosity=0)

        salvo = Produto.objects.get(codigo='REAL-01')
        self.assertEqual(salvo.saldo_cheio, 10)
        self.assertEqual(salvo.saldo_seco, 0)
        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(Cliente.objects.get().total_pedidos, 0)
        self.assertEqual(Pedido.objects.count(), 0)
        self.assertEqual(MovimentacaoEstoque.objects.count(), 0)
        self.assertTrue(User.objects.filter(username=USERNAME_ADMIN).exists())

    def _cliente_real(self):
        return ClienteBusiness().criar(
            {
                'nome': 'Cliente Real da Loja',
                'telefone': '11888887777',
                'telefone_secundario': '',
                'logradouro': 'Rua do Comércio',
                'numero': '10',
                'complemento': '',
                'bairro': 'Centro',
                'cidade': 'São Paulo',
                'ponto_referencia': '',
                'observacoes': 'Cliente atendido no balcão',
            },
            self.admin,
        )
