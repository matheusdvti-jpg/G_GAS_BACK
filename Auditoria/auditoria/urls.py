from django.urls import path

from . import views

app_name = 'auditoria'

urlpatterns = [
    path('listar/', views.ListarAuditoriaListView.as_view(), name='listar'),
    path('<int:pk>/', views.ObterAuditoriaGetView.as_view(), name='detalhe'),
]
