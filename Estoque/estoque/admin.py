from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import MovimentacaoEstoque


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(SimpleHistoryAdmin):
    list_display = ('created_at', 'tipo', 'nome_produto', 'tipo_saldo', 'quantidade', 'saldo_novo')
    list_filter = ('tipo', 'tipo_saldo')
    search_fields = ('nome_produto', 'codigo_pedido', 'nome_usuario')
