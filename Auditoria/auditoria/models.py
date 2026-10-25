from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .business import RegistroAuditoriaBusiness
from .choices import TIPO_ENTIDADE_CHOICES
from .helpers import RegistroAuditoriaHelpers
from .rules import RegistroAuditoriaRules


class RegistroAuditoria(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    helper_class = RegistroAuditoriaHelpers
    business_class = RegistroAuditoriaBusiness
    rules_class = RegistroAuditoriaRules

    acao = models.CharField('Ação', max_length=40)
    tipo_entidade = models.CharField('Tipo', max_length=20, choices=TIPO_ENTIDADE_CHOICES)
    entidade_id = models.CharField('Identificador', max_length=64)
    descricao = models.TextField('Descrição')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Usuário',
        on_delete=models.PROTECT,
        related_name='registros_auditoria',
    )
    nome_usuario = models.CharField('Nome de quem executou', max_length=150)
    alteracoes = models.JSONField('Alterações', default=dict, blank=True)

    class Meta:
        verbose_name = 'Registro de auditoria'
        verbose_name_plural = 'Registros de auditoria'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tipo_entidade', 'entidade_id']),
            models.Index(fields=['acao']),
        ]

    def __str__(self):
        return f'{self.acao} {self.tipo_entidade}#{self.entidade_id}'
