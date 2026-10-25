from django.urls import include, path

urlpatterns = [
    path('', include('Relatorios.relatorios.urls')),
]
