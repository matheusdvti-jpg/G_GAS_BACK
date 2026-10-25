from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase

from Colaboradores.colaboradores.business import ColaboradorBusiness
from Colaboradores.colaboradores.choices import PERFIL_ATENDENTE, PERFIL_ENTREGADOR, PERFIL_GERENTE
from Colaboradores.colaboradores.models import User


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


class LeiturasTests(APITestCase):
    def setUp(self):
        call_command('seed_inicial')
        self.gerente = criar_conta('Marina Gerente', '11144477735', PERFIL_GERENTE, 'marina').conta
        self.atendente = criar_conta('Ana Atendente', '39053344705', PERFIL_ATENDENTE, 'ana').conta
        self.joao = criar_conta('João Entregas', '12345678909', PERFIL_ENTREGADOR, 'joao', 'ABC1D23')

        self.client.force_authenticate(self.gerente)
        produto = self.client.post(
            '/produtos/',
            {
                'codigo': 'GLP-13',
                'nome': 'GLP 13kg',
                'marca': 'Ultragaz',
                'categoria': 'GAS',
                'preco_venda': '115.00',
                'preco_custo': '85.00',
                'saldo_cheio': 10,
                'saldo_seco': 0,
                'estoque_minimo': 20,
                'unidade': 'Unidade',
            },
            format='json',
        )
        self.produto_id = produto.data['data']['id']
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
        pedido = self.client.post(
            '/pedidos/',
            {
                'cliente_id': cliente.data['data']['id'],
                'entregador_id': self.joao.id,
                'itens': [{'produto_id': self.produto_id, 'quantidade': 2, 'vazios_recebidos': 0}],
                'forma_pagamento': 'DINHEIRO',
                'valor_recebido': '300.00',
            },
            format='json',
        )
        self.assertEqual(pedido.status_code, 201, pedido.data)
        self.pedido_id = pedido.data['data']['id']
        self.hoje = timezone.localdate().isoformat()

    def test_painel_e_fechamento_respeitam_perfil_e_cancelamento(self):
        painel = self.client.get('/relatorios/painel/')
        self.assertEqual(painel.status_code, 200)
        dados = painel.data['data']
        self.assertEqual(dados['faturamento_total'], '230.00')
        self.assertEqual(dados['ticket_medio'], '0.00')
        self.assertEqual(dados['pedidos_em_andamento'], 1)
        self.assertEqual(dados['pedidos_entregues'], 0)
        self.assertEqual(dados['estoque_gas'], 8)
        self.assertEqual(dados['alerta_estoque_minimo'][0]['nome'], 'GLP 13kg')
        self.assertEqual(dados['fila_despacho'][0]['codigo'], 'PED-000001')
        self.assertEqual(dados['posicao_deposito'][0]['saldo_seco'], 2)

        negado = self.client.get('/relatorios/periodo/', {'de': self.hoje, 'ate': self.hoje})
        self.assertEqual(negado.status_code, 403)

        self.client.force_authenticate(self.joao.conta)
        entregue = self.client.patch(
            f'/pedidos/{self.pedido_id}/status/',
            {'status': 'ENTREGUE'},
            format='json',
        )
        self.assertEqual(entregue.status_code, 200)

        self.client.force_authenticate(self.atendente)
        depois = self.client.get('/relatorios/painel/').data['data']
        self.assertEqual(depois['ticket_medio'], '230.00')
        self.assertEqual(depois['pedidos_entregues'], 1)
        self.assertEqual(depois['pedidos_entregues_hoje'], 1)
        self.assertEqual(depois['fila_despacho'], [])

        self.client.force_authenticate(self.gerente)
        periodo = self.client.get('/relatorios/periodo/', {'de': self.hoje, 'ate': self.hoje})
        self.assertEqual(periodo.status_code, 200, periodo.data)
        fechamento = periodo.data['data']
        self.assertEqual(fechamento['faturamento_bruto'], '230.00')
        self.assertEqual(fechamento['faturamento_liquido'], '230.00')
        self.assertEqual(fechamento['descontos'], '0.00')
        self.assertEqual(fechamento['volume_pedidos'], 1)
        self.assertEqual(fechamento['ticket_medio'], '230.00')
        dinheiro = next(item for item in fechamento['por_forma_pagamento'] if item['forma'] == 'DINHEIRO')
        self.assertEqual(dinheiro['quantidade'], 1)
        self.assertEqual(dinheiro['percentual'], '100.0')
        self.assertEqual(fechamento['entregadores'][0]['nome'], 'João Entregas')
        self.assertEqual(fechamento['entregadores'][0]['entregues'], 1)
        self.assertEqual(fechamento['produtos_mais_vendidos'][0]['quantidade'], 2)

        lista = self.client.get('/pedidos/listar/', {'de': self.hoje, 'ate': self.hoje})
        self.assertEqual(lista.data['count'], 1)
        self.assertEqual(self.client.get('/relatorios/periodo/', {'de': self.hoje}).status_code, 400)
        self.assertEqual(
            self.client.get('/relatorios/periodo/', {'de': '2026-10-25', 'ate': '2026-10-01'}).status_code,
            400,
        )

        cancelado = self.client.patch(
            f'/pedidos/{self.pedido_id}/status/',
            {'status': 'CANCELADO', 'observacao': 'Cliente desistiu da compra'},
            format='json',
        )
        self.assertEqual(cancelado.status_code, 200)
        painel_cancelado = self.client.get('/relatorios/painel/').data['data']
        self.assertEqual(painel_cancelado['faturamento_total'], '0.00')
        self.assertEqual(painel_cancelado['estoque_gas'], 10)
        fechamento_cancelado = self.client.get(
            '/relatorios/periodo/',
            {'de': self.hoje, 'ate': self.hoje},
        ).data['data']
        self.assertEqual(fechamento_cancelado['faturamento_liquido'], '0.00')
        self.assertEqual(fechamento_cancelado['cancelados'], 1)
        self.assertEqual(fechamento_cancelado['volume_pedidos'], 0)

    def test_de_e_ate_usam_o_dia_de_sao_paulo(self):
        from datetime import datetime, timezone as fuso

        from Pedidos.pedidos.models import Pedido

        pedido = Pedido.objects.get(pk=self.pedido_id)
        pedido.created_at = datetime(2026, 10, 26, 2, 30, tzinfo=fuso.utc)
        pedido.save(update_fields=['created_at'])

        self.client.force_authenticate(self.gerente)
        no_dia = self.client.get('/relatorios/periodo/', {'de': '2026-10-25', 'ate': '2026-10-25'})
        self.assertEqual(no_dia.status_code, 200, no_dia.data)
        self.assertEqual(no_dia.data['data']['pedidos_no_periodo'], 1)
        seguinte = self.client.get('/relatorios/periodo/', {'de': '2026-10-26', 'ate': '2026-10-26'})
        self.assertEqual(seguinte.data['data']['pedidos_no_periodo'], 0)

        lista = self.client.get('/pedidos/listar/', {'de': '2026-10-25', 'ate': '2026-10-25'})
        self.assertEqual(lista.data['count'], 1)
        lista_seguinte = self.client.get('/pedidos/listar/', {'de': '2026-10-26', 'ate': '2026-10-26'})
        self.assertEqual(lista_seguinte.data['count'], 0)
