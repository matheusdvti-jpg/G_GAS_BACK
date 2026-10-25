from django.urls import include, path

urlpatterns = [
    path('', include('Pedidos.pedidos.urls')),
]
