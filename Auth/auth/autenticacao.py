import logging

from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import PermissionDenied

from .models import Sessao

logger = logging.getLogger(__name__)


def exigir_csrf(request) -> None:
    django_request = getattr(request, '_request', request)

    def dummy_get_response(req):
        return None

    check = CsrfViewMiddleware(dummy_get_response)
    check.process_request(django_request)
    motivo = check.process_view(django_request, None, (), {})
    if motivo is not None:
        logger.warning('CSRF recusado. path=%s', getattr(django_request, 'path', '-'))
        raise PermissionDenied('Falha na verificação de CSRF.')


class SessaoAuthentication(BaseAuthentication):
    def authenticate(self, request):
        segredo = request.COOKIES.get(settings.SESSAO_COOKIE_NAME)
        if not segredo:
            return None
        exigir_csrf(request)
        sessao = Sessao.buscar_ativa(segredo)
        if sessao is None or not sessao.usuario.is_active:
            return None
        sessao.registrar_uso()
        return (sessao.usuario, sessao)

    def authenticate_header(self, request):
        return 'Cookie'
