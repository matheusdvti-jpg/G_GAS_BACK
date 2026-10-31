from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .business import ProdutoBusiness
from .choices import CATEGORIA_CHOICES
from .helpers import ProdutoHelpers
from .rules import ProdutoRules


class Produto(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    helper_class = ProdutoHelpers
    business_class = ProdutoBusiness
    rules_class = ProdutoRules

    codigo = models.CharField('Código', max_length=40, unique=True)
    nome = models.CharField('Nome', max_length=150)
    descricao = models.TextField('Descrição', blank=True, default='')
    marca = models.CharField('Marca', max_length=80, blank=True, default='')
    categoria = models.CharField('Categoria', max_length=20, choices=CATEGORIA_CHOICES, blank=True, default='')
    preco_venda = models.DecimalField('Preço', max_digits=10, decimal_places=2)
    preco_custo = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    saldo_cheio = models.PositiveIntegerField('Saldo cheio', default=0)
    saldo_seco = models.PositiveIntegerField('Saldo seco', default=0)
    estoque_minimo = models.PositiveIntegerField('Estoque mínimo', default=0)
    unidade = models.CharField('Unidade', max_length=40, blank=True, default='')
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['nome']

    def __str__(self):
        return f'{self.codigo} — {self.nome}'
