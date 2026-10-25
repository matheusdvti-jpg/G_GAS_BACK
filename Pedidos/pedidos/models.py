from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .business import PedidoBusiness
from .choices import FORMA_PAGAMENTO_CHOICES, STATUS_PEDIDO_CHOICES, TIPO_DESCONTO_CHOICES
from .helpers import PedidoHelpers
from .rules import PedidoRules


class SequenciaPedido(models.Model):
    nome = models.CharField(max_length=40, unique=True)
    ultimo_numero = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Sequência de pedido'
        verbose_name_plural = 'Sequências de pedido'


class Pedido(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    helper_class = PedidoHelpers
    business_class = PedidoBusiness
    rules_class = PedidoRules

    codigo = models.CharField('Código', max_length=20, unique=True)
    cliente = models.ForeignKey(
        'clientes.Cliente',
        verbose_name='Cliente',
        on_delete=models.PROTECT,
        related_name='pedidos',
    )
    nome_cliente = models.CharField('Cliente', max_length=150)
    telefone_cliente = models.CharField('Telefone', max_length=11)
    logradouro = models.CharField('Logradouro', max_length=150)
    numero = models.CharField('Número', max_length=20)
    complemento = models.CharField('Complemento', max_length=80, blank=True, default='')
    bairro = models.CharField('Bairro', max_length=80)
    cidade = models.CharField('Cidade', max_length=80)
    ponto_referencia = models.CharField('Ponto de referência', max_length=150)
    subtotal = models.DecimalField('Subtotal', max_digits=12, decimal_places=2)
    tipo_desconto = models.CharField('Tipo de desconto', max_length=10, choices=TIPO_DESCONTO_CHOICES)
    valor_desconto = models.DecimalField('Desconto', max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField('Total', max_digits=12, decimal_places=2)
    forma_pagamento = models.CharField('Pagamento', max_length=10, choices=FORMA_PAGAMENTO_CHOICES)
    valor_recebido = models.DecimalField(
        'Valor recebido',
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    troco = models.DecimalField('Troco', max_digits=12, decimal_places=2, default=0)
    entregador = models.ForeignKey(
        'colaboradores.Colaborador',
        verbose_name='Entregador',
        on_delete=models.PROTECT,
        related_name='entregas',
    )
    nome_entregador = models.CharField('Entregador', max_length=150)
    status = models.CharField('Status', max_length=20, choices=STATUS_PEDIDO_CHOICES)
    observacoes = models.TextField('Observações', blank=True, default='')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Criado por',
        on_delete=models.PROTECT,
        related_name='pedidos_criados',
    )
    nome_criado_por = models.CharField('Criado por', max_length=150)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['codigo']),
        ]

    def __str__(self):
        return self.codigo


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey('produtos.Produto', on_delete=models.PROTECT, related_name='itens_pedido')
    nome_produto = models.CharField(max_length=150)
    marca = models.CharField(max_length=80)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=12, decimal_places=2)
    vazios_recebidos = models.PositiveIntegerField(default=0)
    nome_vazio = models.CharField(max_length=40, blank=True, default='')

    class Meta:
        verbose_name = 'Item do pedido'
        verbose_name_plural = 'Itens do pedido'

    def __str__(self):
        return f'{self.quantidade} x {self.nome_produto}'


class HistoricoStatusPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='historico', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_PEDIDO_CHOICES)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='historicos_pedido',
    )
    nome_usuario = models.CharField(max_length=150)
    observacao = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico do pedido'
        verbose_name_plural = 'Históricos do pedido'
        ordering = ['created_at']
