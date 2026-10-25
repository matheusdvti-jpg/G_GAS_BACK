from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(SimpleHistoryAdmin):
    list_display = ('created_at', 'acao', 'tipo_entidade', 'entidade_id', 'nome_usuario')
    list_filter = ('tipo_entidade', 'acao')
    search_fields = ('descricao', 'nome_usuario', 'entidade_id')
