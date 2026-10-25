from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Produto


@admin.register(Produto)
class ProdutoAdmin(SimpleHistoryAdmin):
    list_display = ('codigo', 'nome', 'categoria', 'preco_venda', 'saldo_cheio', 'ativo')
    list_filter = ('categoria', 'ativo')
    search_fields = ('codigo', 'nome', 'marca')
