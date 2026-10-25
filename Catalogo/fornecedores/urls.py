from django.urls import path

from . import views

app_name = 'fornecedores'

urlpatterns = [
    path('', views.CadastrarFornecedorPostView.as_view(), name='cadastrar'),
    path('listar/', views.ListarFornecedoresListView.as_view(), name='listar'),
    path('<int:pk>/', views.ObterFornecedorGetView.as_view(), name='detalhe'),
    path('<int:pk>/atualizar/', views.AtualizarFornecedorUpdateView.as_view(), name='atualizar'),
]
