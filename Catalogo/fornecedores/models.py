from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .business import FornecedorBusiness
from .helpers import FornecedorHelpers
from .rules import FornecedorRules


class Fornecedor(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    helper_class = FornecedorHelpers
    business_class = FornecedorBusiness
    rules_class = FornecedorRules

    nome_fantasia = models.CharField('Nome fantasia', max_length=150)
    razao_social = models.CharField('Razão social', max_length=150)
    cnpj = models.CharField('CNPJ', max_length=14, unique=True)
    telefone = models.CharField('Telefone', max_length=11)
    nome_contato = models.CharField('Contato', max_length=150)
    endereco = models.CharField('Endereço', max_length=200)
    cidade = models.CharField('Cidade', max_length=80)
    produtos_fornecidos = models.JSONField('Produtos fornecidos', default=list, blank=True)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        ordering = ['nome_fantasia']

    def __str__(self):
        return self.nome_fantasia
