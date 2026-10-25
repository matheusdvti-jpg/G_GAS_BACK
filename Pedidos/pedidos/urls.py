from django.urls import path

from . import views

app_name = 'pedidos'

urlpatterns = [
    path('', views.CadastrarPedidoPostView.as_view(), name='cadastrar'),
    path('listar/', views.ListarPedidosListView.as_view(), name='listar'),
    path('<int:pk>/', views.ObterPedidoGetView.as_view(), name='detalhe'),
    path('<int:pk>/status/', views.AlterarStatusPedidoUpdateView.as_view(), name='status'),
]
