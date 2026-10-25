from django.urls import path

from . import views

app_name = 'estoque'

urlpatterns = [
    path('movimentacoes/', views.ListarMovimentacoesListView.as_view(), name='listar'),
    path('entradas/', views.RegistrarEntradaPostView.as_view(), name='entrada'),
    path('saidas/', views.RegistrarSaidaPostView.as_view(), name='saida'),
    path('conferencias/', views.RegistrarConferenciaPostView.as_view(), name='conferencia'),
]
