from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Colaborador, User


@admin.register(Colaborador)
class ColaboradorAdmin(SimpleHistoryAdmin):
    list_display = ('nome', 'perfil', 'telefone', 'ativo', 'placa_veiculo')
    list_filter = ('perfil', 'ativo')
    search_fields = ('nome', 'cpf', 'telefone')


@admin.register(User)
class UserAdmin(SimpleHistoryAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
