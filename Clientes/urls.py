from django.urls import include, path

urlpatterns = [
    path('', include('Clientes.clientes.urls')),
]
