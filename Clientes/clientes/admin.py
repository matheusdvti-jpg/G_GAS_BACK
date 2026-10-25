from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(SimpleHistoryAdmin):
    list_display = ('nome', 'telefone', 'bairro', 'cidade', 'total_pedidos')
    search_fields = ('nome', 'telefone', 'bairro', 'cidade')
