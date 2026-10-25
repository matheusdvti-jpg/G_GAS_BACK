from django.urls import include, path

from Auth.auth.views import EuView

app_name = 'auth'

urlpatterns = [
    path('token_jwt/', include('Auth.auth.urls')),
    path('eu/', EuView.as_view(), name='eu'),
]
