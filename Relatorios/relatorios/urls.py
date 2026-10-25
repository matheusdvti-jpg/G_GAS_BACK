from django.urls import path

from . import views

app_name = 'relatorios'

urlpatterns = [
    path('painel/', views.PainelGetView.as_view(), name='painel'),
    path('periodo/', views.PeriodoGetView.as_view(), name='periodo'),
]
