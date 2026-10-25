from decimal import Decimal

from django.db.models import Count, DecimalField, F, Max, Q, Sum
from django.db.models.functions import Coalesce

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from Catalogo.produtos.choices import CATEGORIA_AGUA, CATEGORIA_GAS
from Catalogo.produtos.models import Produto
from Colaboradores.colaboradores.choices import PERFIL_ENTREGADOR
from Colaboradores.colaboradores.models import Colaborador
from Pedidos.pedidos.choices import (
    FORMA_PAGAMENTO_CHOICES,
    STATUS_CANCELADO,
    STATUS_ENTREGUE,
    STATUS_PENDENTE,
)
from Pedidos.pedidos.models import HistoricoStatusPedido, ItemPedido, Pedido


DINHEIRO = DecimalField(max_digits=12, decimal_places=2)


class LeituraHelpers(ModelInstanceHelpers):
    def formatar_dinheiro(self, valor):
        numero = Decimal('0') if valor is None else Decimal(valor)
        return f'{numero.quantize(Decimal("0.01")):.2f}'

    def formatar_percentual(self, parte, todo):
        if not todo:
            return '0.0'
        percentual = (Decimal(parte) / Decimal(todo)) * Decimal('100')
        return f'{percentual.quantize(Decimal("0.1")):.1f}'

    def pedidos_no_periodo(self, inicio, fim):
        consulta = Pedido.objects.all()
        if inicio and fim:
            consulta = consulta.filter(created_at__date__gte=inicio, created_at__date__lte=fim)
        return consulta

    def resumo_pedidos(self, consulta):
        validos = ~Q(status=STATUS_CANCELADO)
        return consulta.aggregate(
            faturamento=Coalesce(Sum('total', filter=validos), Decimal('0'), output_field=DINHEIRO),
            bruto=Coalesce(Sum('subtotal', filter=validos), Decimal('0'), output_field=DINHEIRO),
            descontos=Coalesce(Sum('valor_desconto', filter=validos), Decimal('0'), output_field=DINHEIRO),
            validos=Count('id', filter=validos),
            entregues=Count('id', filter=Q(status=STATUS_ENTREGUE)),
            pendentes=Count('id', filter=Q(status=STATUS_PENDENTE)),
            cancelados=Count('id', filter=Q(status=STATUS_CANCELADO)),
        )

    def entregues_hoje(self, dia):
        return (
            HistoricoStatusPedido.objects.filter(status=STATUS_ENTREGUE, created_at__date=dia)
            .values('pedido_id')
            .distinct()
            .count()
        )

    def estoque(self):
        ativos = Produto.objects.filter(ativo=True)
        totais = ativos.aggregate(
            gas=Coalesce(Sum('saldo_cheio', filter=Q(categoria=CATEGORIA_GAS)), 0),
            agua=Coalesce(Sum('saldo_cheio', filter=Q(categoria=CATEGORIA_AGUA)), 0),
        )
        alerta = ativos.filter(saldo_cheio__lte=F('estoque_minimo')).order_by('nome')
        return totais, alerta, ativos.order_by('nome')

    def fila_despacho(self):
        return (
            Pedido.objects.filter(status=STATUS_PENDENTE)
            .prefetch_related('itens')
            .order_by('created_at')
        )

    def por_pagamento(self, validos):
        linhas = validos.values('forma_pagamento').annotate(
            quantidade=Count('id'),
            total=Coalesce(Sum('total'), Decimal('0'), output_field=DINHEIRO),
        )
        return {linha['forma_pagamento']: linha for linha in linhas}

    def por_entregador(self, consulta):
        validos = ~Q(status=STATUS_CANCELADO)
        linhas = consulta.values('entregador_id').annotate(
            entregues=Count('id', filter=Q(status=STATUS_ENTREGUE)),
            pendentes=Count('id', filter=Q(status=STATUS_PENDENTE)),
            faturamento=Coalesce(Sum('total', filter=validos), Decimal('0'), output_field=DINHEIRO),
        )
        return {linha['entregador_id']: linha for linha in linhas}

    def entregadores(self):
        return Colaborador.objects.filter(perfil=PERFIL_ENTREGADOR).order_by('nome')

    def produtos_vendidos(self, validos):
        return (
            ItemPedido.objects.filter(pedido__in=validos)
            .values('produto_id')
            .annotate(
                nome=Max('nome_produto'),
                marca=Max('marca'),
                quantidade=Sum('quantidade'),
                faturamento=Coalesce(Sum('total'), Decimal('0'), output_field=DINHEIRO),
            )
            .order_by('-quantidade', 'nome')
        )
