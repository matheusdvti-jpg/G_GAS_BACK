from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .business import ClienteBusiness
from .helpers import ClienteHelpers
from .rules import ClienteRules


class Cliente(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    helper_class = ClienteHelpers
    business_class = ClienteBusiness
    rules_class = ClienteRules

    nome = models.CharField('Nome', max_length=150)
    telefone = models.CharField('Telefone', max_length=11)
    telefone_secundario = models.CharField('Telefone secundário', max_length=11, blank=True, default='')
    logradouro = models.CharField('Endereço', max_length=150)
    numero = models.CharField('Número', max_length=20, blank=True, default='')
    complemento = models.CharField('Complemento', max_length=80, blank=True, default='')
    bairro = models.CharField('Bairro', max_length=80, blank=True, default='')
    cidade = models.CharField('Cidade', max_length=80, blank=True, default='')
    ponto_referencia = models.CharField('Ponto de referência', max_length=150, blank=True, default='')
    observacoes = models.TextField('Observações', blank=True, default='')
    total_pedidos = models.PositiveIntegerField('Total de pedidos', default=0)
    total_gasto = models.DecimalField('Total gasto', max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['telefone']),
            models.Index(fields=['nome']),
        ]

    def __str__(self):
        return self.nome
