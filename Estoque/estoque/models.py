from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .business import MovimentacaoBusiness
from .choices import TIPO_MOVIMENTACAO_CHOICES, TIPO_SALDO_CHOICES
from .helpers import MovimentacaoHelpers
from .rules import MovimentacaoRules


class MovimentacaoEstoque(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    helper_class = MovimentacaoHelpers
    business_class = MovimentacaoBusiness
    rules_class = MovimentacaoRules

    produto = models.ForeignKey(
        'produtos.Produto',
        verbose_name='Produto',
        on_delete=models.PROTECT,
        related_name='movimentacoes',
    )
    nome_produto = models.CharField('Produto', max_length=150)
    tipo = models.CharField('Tipo', max_length=40, choices=TIPO_MOVIMENTACAO_CHOICES)
    tipo_saldo = models.CharField('Saldo', max_length=10, choices=TIPO_SALDO_CHOICES)
    quantidade = models.IntegerField('Quantidade')
    saldo_anterior = models.PositiveIntegerField('Saldo anterior')
    saldo_novo = models.PositiveIntegerField('Saldo novo')
    custo_unitario = models.DecimalField(
        'Custo unitário',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    fornecedor = models.ForeignKey(
        'fornecedores.Fornecedor',
        verbose_name='Fornecedor',
        on_delete=models.PROTECT,
        related_name='movimentacoes',
        null=True,
        blank=True,
    )
    nome_fornecedor = models.CharField('Fornecedor', max_length=150, blank=True, default='')
    cliente = models.ForeignKey(
        'clientes.Cliente',
        verbose_name='Cliente',
        on_delete=models.PROTECT,
        related_name='movimentacoes',
        null=True,
        blank=True,
    )
    nome_cliente = models.CharField('Cliente', max_length=150, blank=True, default='')
    pedido_id = models.PositiveIntegerField('Pedido', null=True, blank=True)
    codigo_pedido = models.CharField('Código do pedido', max_length=20, blank=True, default='')
    motivo = models.TextField('Motivo', blank=True, default='')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Usuário',
        on_delete=models.PROTECT,
        related_name='movimentacoes_estoque',
    )
    nome_usuario = models.CharField('Quem executou', max_length=150)

    class Meta:
        verbose_name = 'Movimentação de estoque'
        verbose_name_plural = 'Movimentações de estoque'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tipo']),
            models.Index(fields=['pedido_id']),
        ]

    def __str__(self):
        return f'{self.tipo} {self.nome_produto} ({self.quantidade})'
