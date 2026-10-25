from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Fornecedor


@admin.register(Fornecedor)
class FornecedorAdmin(SimpleHistoryAdmin):
    list_display = ('nome_fantasia', 'cnpj', 'cidade', 'ativo')
    list_filter = ('ativo', 'cidade')
    search_fields = ('nome_fantasia', 'razao_social', 'cnpj')
