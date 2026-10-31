from django.conf import settings
from rest_framework.authentication import BaseAuthentication

from .models import Sessao


class SessaoAuthentication(BaseAuthentication):
    def authenticate(self, request):
        segredo = request.COOKIES.get(settings.SESSAO_COOKIE_NAME)
        if not segredo:
            return None
        sessao = Sessao.buscar_ativa(segredo)
        if sessao is None or not sessao.usuario.is_active:
            return None
        return (sessao.usuario, sessao)

    def authenticate_header(self, request):
        return 'Cookie'
