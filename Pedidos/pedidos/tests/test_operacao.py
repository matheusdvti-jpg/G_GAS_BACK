from django.core.management import call_command
from rest_framework.test import APITestCase

from Auditoria.auditoria.models import RegistroAuditoria
from Catalogo.produtos.models import Produto
from Clientes.clientes.models import Cliente
from Colaboradores.colaboradores.business import ColaboradorBusiness
from Colaboradores.colaboradores.choices import (
    PERFIL_ATENDENTE,
    PERFIL_ENTREGADOR,
    PERFIL_ESTOQUISTA,
    PERFIL_GERENTE,
)
from Colaboradores.colaboradores.models import User
from Estoque.estoque.models import MovimentacaoEstoque


def criar_conta(nome, cpf, perfil, username, placa=''):
    return ColaboradorBusiness().criar(
        {
            'nome': nome,
            'cpf': cpf,
            'telefone': '11999998888',
            'perfil': perfil,
            'ativo': True,
            'placa_veiculo': placa,
            'conta': {
                'username': username,
                'email': f'{username}@ggas.com.br',
                'password': 'Perfil@123',
            },
        }
    )


class EstoqueEPedidosTests(APITestCase):
    def setUp(self):
        call_command('seed_inicial')
        self.admin = User.objects.get(username='admin')
        self.gerente = criar_conta('Marina Gerente', '11144477735', PERFIL_GERENTE, 'marina').conta
        self.atendente = criar_conta('Ana Atendente', '39053344705', PERFIL_ATENDENTE, 'ana').conta
        self.estoquista = criar_conta('Carlos Estoque', '15350946056', PERFIL_ESTOQUISTA, 'carlos').conta
        self.joao = criar_conta('João Entregas', '12345678909', PERFIL_ENTREGADOR, 'joao', 'ABC1D23')
        self.maria = criar_conta('Maria Entregas', '12345678810', PERFIL_ENTREGADOR, 'maria', 'XYZ2E34')

        self.client.force_authenticate(self.gerente)
        produto = self.client.post('/produtos/', self._produto('GLP-13', 'GLP 13kg', 'GAS', 10), format='json')
        self.produto_id = produto.data['data']['id']
        agua = self.client.post('/produtos/', self._produto('AGUA-20', 'Galão 20L', 'AGUA', 5), format='json')
        self.agua_id = agua.data['data']['id']
        fornecedor = self.client.post(
            '/fornecedores/',
            {
                'nome_fantasia': 'Ultragaz',
                'razao_social': 'Companhia Ultragaz S.A.',
                'cnpj': '11222333000181',
                'telefone': '1133334444',
                'nome_contato': 'Paulo Compras',
                'endereco': 'Avenida Paulista, 1000',
                'cidade': 'São Paulo',
            },
            format='json',
        )
        self.fornecedor_id = fornecedor.data['data']['id']

        self.client.force_authenticate(self.atendente)
        cliente = self.client.post(
            '/clientes/',
            {
                'nome': 'Maria da Silva',
                'telefone': '11988887777',
                'logradouro': 'Rua das Flores',
                'numero': '120',
                'bairro': 'Centro',
                'cidade': 'São Paulo',
                'ponto_referencia': 'Em frente à padaria',
            },
            format='json',
        )
        self.cliente_id = cliente.data['data']['id']

    def test_estoquista_movimenta_saldo_e_atendente_nao_lanca(self):
        self.client.force_authenticate(self.atendente)
        negado = self.client.post(
            '/estoque/entradas/',
            {
                'produto_id': self.produto_id,
                'fornecedor_id': self.fornecedor_id,
                'quantidade': 5,
                'custo_unitario': '80.00',
            },
            format='json',
        )
        self.assertEqual(negado.status_code, 403)

        self.client.force_authenticate(self.estoquista)
        entrada = self.client.post(
            '/estoque/entradas/',
            {
                'produto_id': self.produto_id,
                'fornecedor_id': self.fornecedor_id,
                'quantidade': 5,
                'custo_unitario': '80.00',
                'motivo': 'Carga da manhã',
            },
            format='json',
        )
        self.assertEqual(entrada.status_code, 201)
        self.assertEqual(entrada.data['data']['saldo_novo'], 15)
        self.assertEqual(Produto.objects.get(pk=self.produto_id).saldo_cheio, 15)

        sem_motivo = self.client.post(
            '/estoque/saidas/',
            {
                'produto_id': self.produto_id,
                'quantidade': 2,
                'tipo': 'SAIDA_MANUAL_PERDA',
                'motivo': 'x',
            },
            format='json',
        )
        self.assertEqual(sem_motivo.status_code, 400)

        saida = self.client.post(
            '/estoque/saidas/',
            {
                'produto_id': self.produto_id,
                'quantidade': 2,
                'tipo': 'SAIDA_MANUAL_PERDA',
                'motivo': 'Botijão amassado no pátio',
            },
            format='json',
        )
        self.assertEqual(saida.status_code, 201)
        self.assertEqual(saida.data['data']['quantidade'], -2)

        emprestimo = self.client.post(
            '/estoque/saidas/',
            {
                'produto_id': self.produto_id,
                'quantidade': 1,
                'tipo': 'SAIDA_MANUAL_EMPRESTIMO',
                'motivo': 'Empréstimo combinado',
            },
            format='json',
        )
        self.assertEqual(emprestimo.status_code, 400)

        emprestimo_ok = self.client.post(
            '/estoque/saidas/',
            {
                'produto_id': self.produto_id,
                'quantidade': 1,
                'tipo': 'SAIDA_MANUAL_EMPRESTIMO',
                'motivo': 'Empréstimo combinado',
                'cliente_id': self.cliente_id,
            },
            format='json',
        )
        self.assertEqual(emprestimo_ok.status_code, 201)

        conferencia = self.client.post(
            '/estoque/conferencias/',
            {
                'produto_id': self.produto_id,
                'contagem': 10,
                'motivo': 'Contagem do fim do turno',
            },
            format='json',
        )
        self.assertEqual(conferencia.status_code, 201)
        self.assertEqual(Produto.objects.get(pk=self.produto_id).saldo_cheio, 10)

        self.client.force_authenticate(self.gerente)
        bloqueio = self.client.patch(
            f'/produtos/{self.produto_id}/atualizar/',
            {'saldo_cheio': 99},
            format='json',
        )
        self.assertEqual(bloqueio.status_code, 400)

    def test_patch_com_saldo_velho_nao_desfaz_a_venda(self):
        self.client.force_authenticate(self.atendente)
        venda = self.client.post('/pedidos/', self._venda(self.produto_id, 2, '300.00'), format='json')
        self.assertEqual(venda.status_code, 201, venda.data)
        self.assertEqual(Produto.objects.get(pk=self.produto_id).saldo_cheio, 8)

        self.client.force_authenticate(self.gerente)
        formulario_velho = self.client.patch(
            f'/produtos/{self.produto_id}/atualizar/',
            {'nome': 'GLP 13kg revisado', 'saldo_cheio': 10},
            format='json',
        )
        self.assertEqual(formulario_velho.status_code, 400)
        produto = Produto.objects.get(pk=self.produto_id)
        self.assertEqual(produto.saldo_cheio, 8)
        self.assertEqual(produto.saldo_seco, 2)

        atualizado = self.client.patch(
            f'/produtos/{self.produto_id}/atualizar/',
            {'nome': 'GLP 13kg revisado'},
            format='json',
        )
        self.assertEqual(atualizado.status_code, 200, atualizado.data)
        produto.refresh_from_db()
        self.assertEqual(produto.nome, 'GLP 13kg revisado')
        self.assertEqual(produto.saldo_cheio, 8)
        self.assertEqual(produto.saldo_seco, 2)

    def test_venda_baixa_cheio_recebe_seco_e_cancelamento_estorna(self):
        self.client.force_authenticate(self.atendente)
        pedido = self.client.post('/pedidos/', self._venda(self.produto_id, 2, '300.00'), format='json')
        self.assertEqual(pedido.status_code, 201, pedido.data)
        dados = pedido.data['data']
        self.assertEqual(dados['codigo'], 'PED-000001')
        self.assertEqual(dados['status'], 'PENDENTE')
        self.assertEqual(dados['total'], '230.00')
        self.assertEqual(dados['troco'], '70.00')
        self.assertEqual(dados['ponto_referencia'], 'Em frente à padaria')
        self.assertEqual(dados['itens'][0]['vazios_recebidos'], 2)
        self.assertEqual(dados['itens'][0]['nome_vazio'], 'botijão seco')

        produto = Produto.objects.get(pk=self.produto_id)
        self.assertEqual(produto.saldo_cheio, 8)
        self.assertEqual(produto.saldo_seco, 2)
        cliente = Cliente.objects.get(pk=self.cliente_id)
        self.assertEqual(cliente.total_pedidos, 1)
        self.assertEqual(str(cliente.total_gasto), '230.00')

        agua = self.client.post(
            '/pedidos/',
            self._venda(self.agua_id, 2, '80.00', vazios=1),
            format='json',
        )
        self.assertEqual(agua.status_code, 400)

        self.client.force_authenticate(self.estoquista)
        self.assertEqual(
            self.client.post('/pedidos/', self._venda(self.produto_id, 1, '115.00'), format='json').status_code,
            403,
        )

        self.client.force_authenticate(self.atendente)
        cancelado_pelo_atendente = self.client.patch(
            f"/pedidos/{dados['id']}/status/",
            {'status': 'CANCELADO', 'observacao': 'Cliente desistiu'},
            format='json',
        )
        self.assertEqual(cancelado_pelo_atendente.status_code, 403)

        self.client.force_authenticate(self.maria.conta)
        outro_entregador = self.client.patch(
            f"/pedidos/{dados['id']}/status/",
            {'status': 'ENTREGUE'},
            format='json',
        )
        self.assertEqual(outro_entregador.status_code, 403)

        self.client.force_authenticate(self.joao.conta)
        entregue = self.client.patch(
            f"/pedidos/{dados['id']}/status/",
            {'status': 'ENTREGUE', 'observacao': 'Entrega confirmada'},
            format='json',
        )
        self.assertEqual(entregue.status_code, 200)
        self.assertEqual(entregue.data['data']['status'], 'ENTREGUE')

        self.client.force_authenticate(self.gerente)
        reaberto = self.client.patch(
            f"/pedidos/{dados['id']}/status/",
            {'status': 'PENDENTE', 'observacao': 'Reaberto para nova saída'},
            format='json',
        )
        self.assertEqual(reaberto.status_code, 200)

        sem_motivo = self.client.patch(
            f"/pedidos/{dados['id']}/status/",
            {'status': 'CANCELADO', 'observacao': 'ok'},
            format='json',
        )
        self.assertEqual(sem_motivo.status_code, 400)

        cancelado = self.client.patch(
            f"/pedidos/{dados['id']}/status/",
            {'status': 'CANCELADO', 'observacao': 'Cliente desistiu da compra'},
            format='json',
        )
        self.assertEqual(cancelado.status_code, 200)
        produto.refresh_from_db()
        self.assertEqual(produto.saldo_cheio, 10)
        self.assertEqual(produto.saldo_seco, 0)
        cliente.refresh_from_db()
        self.assertEqual(cliente.total_pedidos, 1)
        self.assertEqual(str(cliente.total_gasto), '230.00')

        com_desconto = self.client.post(
            '/pedidos/',
            {
                **self._venda(self.produto_id, 1, '115.00'),
                'tipo_desconto': 'PERCENT',
                'valor_desconto': '10',
            },
            format='json',
        )
        self.assertEqual(com_desconto.status_code, 201)
        self.assertEqual(com_desconto.data['data']['codigo'], 'PED-000002')
        self.assertEqual(com_desconto.data['data']['valor_desconto'], '11.50')
        self.assertEqual(com_desconto.data['data']['total'], '103.50')

        self.client.force_authenticate(self.admin)
        auditoria = self.client.get('/auditoria/listar/', {'tipo_entidade': 'PEDIDO', 'acao': 'CRIAR_PEDIDO'})
        self.assertGreaterEqual(auditoria.data['count'], 1)

    def test_agua_acessorio_e_piso_do_seco_mantem_o_lancamento(self):
        self.client.force_authenticate(self.gerente)
        acessorio = self.client.post(
            '/produtos/',
            self._produto('REG-01', 'Registro', 'ACESSORIO', 4),
            format='json',
        )
        self.assertEqual(acessorio.status_code, 201, acessorio.data)
        acessorio_id = acessorio.data['data']['id']

        self.client.force_authenticate(self.atendente)
        agua = self.client.post(
            '/pedidos/',
            self._venda(self.agua_id, 2, '80.00', vazios=2),
            format='json',
        )
        self.assertEqual(agua.status_code, 201, agua.data)
        self.assertEqual(agua.data['data']['itens'][0]['vazios_recebidos'], 2)
        self.assertEqual(agua.data['data']['itens'][0]['nome_vazio'], 'galão vazio')

        peca = self.client.post(
            '/pedidos/',
            self._venda(acessorio_id, 1, '40.00'),
            format='json',
        )
        self.assertEqual(peca.status_code, 201, peca.data)
        self.assertEqual(peca.data['data']['itens'][0]['vazios_recebidos'], 0)
        self.assertEqual(peca.data['data']['itens'][0]['nome_vazio'], '')

        agua_db = Produto.objects.get(pk=self.agua_id)
        self.assertEqual(agua_db.saldo_cheio, 3)
        self.assertEqual(agua_db.saldo_seco, 2)
        peca_db = Produto.objects.get(pk=acessorio_id)
        self.assertEqual(peca_db.saldo_cheio, 3)
        self.assertEqual(peca_db.saldo_seco, 0)

        gas = self.client.post('/pedidos/', self._venda(self.produto_id, 2, '300.00'), format='json')
        self.assertEqual(gas.status_code, 201, gas.data)
        produto = Produto.objects.get(pk=self.produto_id)
        produto.saldo_seco = 1
        produto.save(update_fields=['saldo_seco', 'updated_at'])

        self.client.force_authenticate(self.gerente)
        cancelado = self.client.patch(
            f"/pedidos/{gas.data['data']['id']}/status/",
            {'status': 'CANCELADO', 'observacao': 'Cliente desistiu da compra'},
            format='json',
        )
        self.assertEqual(cancelado.status_code, 200, cancelado.data)
        produto.refresh_from_db()
        self.assertEqual(produto.saldo_cheio, 10)
        self.assertEqual(produto.saldo_seco, 0)

        movimentos = MovimentacaoEstoque.objects.filter(
            produto_id__in=[self.agua_id, acessorio_id, self.produto_id]
        )
        self.assertGreater(movimentos.count(), 0)
        for movimento in movimentos:
            self.assertEqual(movimento.saldo_anterior + movimento.quantidade, movimento.saldo_novo)
            self.assertGreaterEqual(movimento.saldo_novo, 0)

        saida_seco = movimentos.get(
            pedido_id=gas.data['data']['id'],
            tipo='SAIDA_VAZIO_DEVOLUCAO',
        )
        self.assertEqual(saida_seco.quantidade, -1)
        self.assertEqual(saida_seco.saldo_anterior, 1)
        self.assertFalse(RegistroAuditoria.objects.filter(tipo_entidade='ESTOQUE').exists())

    def test_status_e_perfil_seguem_a_matriz(self):
        self.client.force_authenticate(self.atendente)
        pedido = self.client.post('/pedidos/', self._venda(self.produto_id, 1, '115.00'), format='json')
        self.assertEqual(pedido.status_code, 201, pedido.data)
        endereco = f"/pedidos/{pedido.data['data']['id']}/status/"

        for conta in (self.atendente, self.estoquista, self.maria.conta):
            self.client.force_authenticate(conta)
            confirmacao = self.client.patch(endereco, {'status': 'ENTREGUE'}, format='json')
            self.assertEqual(confirmacao.status_code, 403, confirmacao.data)

        self.client.force_authenticate(self.gerente)
        entregue = self.client.patch(endereco, {'status': 'ENTREGUE'}, format='json')
        self.assertEqual(entregue.status_code, 200, entregue.data)

        for conta in (self.atendente, self.joao.conta, self.maria.conta):
            self.client.force_authenticate(conta)
            reabertura = self.client.patch(endereco, {'status': 'PENDENTE'}, format='json')
            self.assertEqual(reabertura.status_code, 403, reabertura.data)

        self.client.force_authenticate(self.gerente)
        invalido = self.client.patch(endereco, {'status': 'NOVO'}, format='json')
        self.assertEqual(invalido.status_code, 400, invalido.data)

        cancelado = self.client.patch(
            endereco,
            {'status': 'CANCELADO', 'observacao': 'Cliente desistiu da compra'},
            format='json',
        )
        self.assertEqual(cancelado.status_code, 200, cancelado.data)
        depois = self.client.patch(endereco, {'status': 'ENTREGUE'}, format='json')
        self.assertEqual(depois.status_code, 400, depois.data)
        detalhe = self.client.get(f"/pedidos/{pedido.data['data']['id']}/")
        self.assertEqual(detalhe.data['data']['status'], 'CANCELADO')
        segundo = self.client.patch(
            endereco,
            {'status': 'CANCELADO', 'observacao': 'Cliente desistiu da compra'},
            format='json',
        )
        self.assertEqual(segundo.status_code, 200, segundo.data)
        produto = Produto.objects.get(pk=self.produto_id)
        self.assertEqual(produto.saldo_cheio, 10)
        self.assertEqual(produto.saldo_seco, 0)
        self.assertEqual(
            MovimentacaoEstoque.objects.filter(
                pedido_id=pedido.data['data']['id'],
                tipo='ESTORNO_CANCELAMENTO',
            ).count(),
            1,
        )

        self.client.force_authenticate(self.atendente)
        cliente_ausente = self.client.post(
            '/pedidos/',
            {**self._venda(self.produto_id, 1, '115.00'), 'cliente_id': 999999},
            format='json',
        )
        self.assertEqual(cliente_ausente.status_code, 400, cliente_ausente.data)

        self.client.force_authenticate(self.estoquista)
        produto_ausente = self.client.post(
            '/estoque/entradas/',
            {
                'produto_id': 999999,
                'fornecedor_id': self.fornecedor_id,
                'quantidade': 1,
                'custo_unitario': '10.00',
            },
            format='json',
        )
        self.assertEqual(produto_ausente.status_code, 404, produto_ausente.data)

    def _produto(self, codigo, nome, categoria, saldo):
        return {
            'codigo': codigo,
            'nome': nome,
            'marca': 'Ultragaz',
            'categoria': categoria,
            'preco_venda': '115.00' if categoria == 'GAS' else '40.00',
            'preco_custo': '85.00' if categoria == 'GAS' else '18.00',
            'saldo_cheio': saldo,
            'saldo_seco': 0,
            'estoque_minimo': 2,
            'unidade': 'Unidade',
        }

    def _venda(self, produto_id, quantidade, recebido, vazios=0):
        return {
            'cliente_id': self.cliente_id,
            'entregador_id': self.joao.id,
            'itens': [
                {
                    'produto_id': produto_id,
                    'quantidade': quantidade,
                    'vazios_recebidos': vazios,
                }
            ],
            'forma_pagamento': 'DINHEIRO',
            'valor_recebido': recebido,
        }
