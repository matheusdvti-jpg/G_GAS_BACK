from django.urls import path

from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.CadastrarClientePostView.as_view(), name='cadastrar'),
    path('listar/', views.ListarClientesListView.as_view(), name='listar'),
    path('<int:pk>/', views.ObterClienteGetView.as_view(), name='detalhe'),
    path('<int:pk>/atualizar/', views.AtualizarClienteUpdateView.as_view(), name='atualizar'),
]
