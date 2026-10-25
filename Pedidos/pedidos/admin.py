from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import ItemPedido, Pedido


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0


@admin.register(Pedido)
class PedidoAdmin(SimpleHistoryAdmin):
    list_display = ('codigo', 'nome_cliente', 'status', 'total', 'nome_entregador', 'created_at')
    list_filter = ('status', 'forma_pagamento')
    search_fields = ('codigo', 'nome_cliente', 'telefone_cliente')
    inlines = [ItemPedidoInline]
