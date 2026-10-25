from django.urls import path

from . import views

app_name = 'colaboradores'

urlpatterns = [
    path('', views.CadastrarColaboradorPostView.as_view(), name='cadastrar'),
    path('listar/', views.ListarColaboradoresListView.as_view(), name='listar'),
    path('<int:pk>/', views.ObterColaboradorGetView.as_view(), name='detalhe'),
    path('<int:pk>/atualizar/', views.AtualizarColaboradorUpdateView.as_view(), name='atualizar'),
    path('<int:pk>/conta/', views.CadastrarContaPostView.as_view(), name='criar-conta'),
    path('<int:pk>/conta/atualizar/', views.AtualizarContaUpdateView.as_view(), name='atualizar-conta'),
]
