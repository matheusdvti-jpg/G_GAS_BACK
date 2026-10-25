from django.urls import path

from . import views

app_name = 'produtos'

urlpatterns = [
    path('', views.CadastrarProdutoPostView.as_view(), name='cadastrar'),
    path('listar/', views.ListarProdutosListView.as_view(), name='listar'),
    path('<int:pk>/', views.ObterProdutoGetView.as_view(), name='detalhe'),
    path('<int:pk>/atualizar/', views.AtualizarProdutoUpdateView.as_view(), name='atualizar'),
]
