from decimal import Decimal

from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness

from Pedidos.pedidos.choices import FORMA_PAGAMENTO_CHOICES, STATUS_CANCELADO

from .helpers import LeituraHelpers
from .rules import LeituraRules


class LeituraBusiness(ModelInstanceBusiness):
    def __init__(self):
        super().__init__(None)
        self.helpers = LeituraHelpers()
        self.rules = LeituraRules()

    def painel(self):
        resumo = self.helpers.resumo_pedidos(self.helpers.pedidos_no_periodo(None, None))
        faturamento = resumo['faturamento']
        ticket = Decimal('0')
        if resumo['entregues'] and resumo['validos']:
            ticket = Decimal(faturamento) / Decimal(resumo['validos'])
        totais, alerta, produtos = self.helpers.estoque()
        return {
            'faturamento_total': self.helpers.formatar_dinheiro(faturamento),
            'ticket_medio': self.helpers.formatar_dinheiro(ticket),
            'pedidos_em_andamento': resumo['pendentes'],
            'pedidos_entregues': resumo['entregues'],
            'pedidos_entregues_hoje': self.helpers.entregues_hoje(timezone.localdate()),
            'estoque_gas': totais['gas'],
            'estoque_agua': totais['agua'],
            'alerta_estoque_minimo': [
                {
                    'id': produto.id,
                    'nome': produto.nome,
                    'saldo_cheio': produto.saldo_cheio,
                    'estoque_minimo': produto.estoque_minimo,
                }
                for produto in alerta
            ],
            'fila_despacho': [self._pedido_fila(pedido) for pedido in self.helpers.fila_despacho()],
            'posicao_deposito': [
                {
                    'id': produto.id,
                    'nome': produto.nome,
                    'marca': produto.marca,
                    'categoria': produto.categoria,
                    'unidade': produto.unidade,
                    'saldo_cheio': produto.saldo_cheio,
                    'saldo_seco': produto.saldo_seco,
                    'estoque_minimo': produto.estoque_minimo,
                }
                for produto in produtos
            ],
        }

    def periodo(self, inicio_texto, fim_texto):
        inicio = self.rules.interpretar_data(inicio_texto)
        fim = self.rules.interpretar_data(fim_texto)
        self.rules.validar_periodo(inicio, fim)
        consulta = self.helpers.pedidos_no_periodo(inicio, fim)
        resumo = self.helpers.resumo_pedidos(consulta)
        liquido = resumo['faturamento']
        ticket = Decimal('0')
        if resumo['validos']:
            ticket = Decimal(liquido) / Decimal(resumo['validos'])
        validos = consulta.exclude(status=STATUS_CANCELADO)
        pagamentos = self.helpers.por_pagamento(validos)
        desempenho = self.helpers.por_entregador(consulta)
        return {
            'de': None if inicio is None else inicio.isoformat(),
            'ate': None if fim is None else fim.isoformat(),
            'pedidos_no_periodo': consulta.count(),
            'faturamento_bruto': self.helpers.formatar_dinheiro(resumo['bruto']),
            'descontos': self.helpers.formatar_dinheiro(resumo['descontos']),
            'faturamento_liquido': self.helpers.formatar_dinheiro(liquido),
            'volume_pedidos': resumo['validos'],
            'cancelados': resumo['cancelados'],
            'ticket_medio': self.helpers.formatar_dinheiro(ticket),
            'por_forma_pagamento': self._pagamentos(pagamentos, liquido),
            'entregadores': self._entregadores(desempenho),
            'produtos_mais_vendidos': [
                {
                    'produto_id': linha['produto_id'],
                    'nome': linha['nome'],
                    'marca': linha['marca'],
                    'quantidade': linha['quantidade'],
                    'faturamento': self.helpers.formatar_dinheiro(linha['faturamento']),
                }
                for linha in self.helpers.produtos_vendidos(validos)
            ],
        }

    def _pedido_fila(self, pedido):
        return {
            'id': pedido.id,
            'codigo': pedido.codigo,
            'nome_cliente': pedido.nome_cliente,
            'logradouro': pedido.logradouro,
            'numero': pedido.numero,
            'bairro': pedido.bairro,
            'nome_entregador': pedido.nome_entregador,
            'total': self.helpers.formatar_dinheiro(pedido.total),
            'itens': [
                {'quantidade': item.quantidade, 'nome_produto': item.nome_produto}
                for item in pedido.itens.all()
            ],
        }

    def _pagamentos(self, pagamentos, liquido):
        linhas = []
        for forma, _rotulo in FORMA_PAGAMENTO_CHOICES:
            linha = pagamentos.get(forma, {})
            total = linha.get('total') or Decimal('0')
            linhas.append(
                {
                    'forma': forma,
                    'quantidade': linha.get('quantidade', 0),
                    'total': self.helpers.formatar_dinheiro(total),
                    'percentual': self.helpers.formatar_percentual(total, liquido),
                }
            )
        ordem = ['PIX', 'DINHEIRO', 'DEBITO', 'CREDITO']
        return sorted(linhas, key=lambda linha: ordem.index(linha['forma']))

    def _entregadores(self, desempenho):
        linhas = []
        for colaborador in self.helpers.entregadores():
            linha = desempenho.get(colaborador.id, {})
            linhas.append(
                {
                    'id': colaborador.id,
                    'nome': colaborador.nome,
                    'placa_veiculo': colaborador.placa_veiculo,
                    'ativo': colaborador.ativo,
                    'entregues': linha.get('entregues', 0),
                    'pendentes': linha.get('pendentes', 0),
                    'faturamento': self.helpers.formatar_dinheiro(linha.get('faturamento')),
                }
            )
        return linhas
