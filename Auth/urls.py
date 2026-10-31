from django.urls import include, path

from Auth.auth.views import EuView, SairView

app_name = 'auth'

urlpatterns = [
    path('token_jwt/', include('Auth.auth.urls')),
    path('eu/', EuView.as_view(), name='eu'),
    path('sair/', SairView.as_view(), name='sair'),
]
