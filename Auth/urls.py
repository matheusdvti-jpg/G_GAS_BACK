from django.urls import include, path

from Auth.auth.views import CsrfView, EuView, SairView

app_name = 'auth'

urlpatterns = [
    path('csrf/', CsrfView.as_view(), name='csrf'),
    path('token_jwt/', include('Auth.auth.urls')),
    path('eu/', EuView.as_view(), name='eu'),
    path('sair/', SairView.as_view(), name='sair'),
]
