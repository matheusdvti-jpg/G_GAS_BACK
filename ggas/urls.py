from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from ggas.views import HealthView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', HealthView.as_view(), name='health'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('auth/', include('Auth.urls')),
    path('colaboradores/', include('Colaboradores.urls')),
    path('clientes/', include('Clientes.urls')),
    path('produtos/', include('Catalogo.produtos.urls')),
    path('fornecedores/', include('Catalogo.fornecedores.urls')),
    path('auditoria/', include('Auditoria.urls')),
    path('estoque/', include('Estoque.urls')),
    path('pedidos/', include('Pedidos.urls')),
    path('relatorios/', include('Relatorios.urls')),
]
