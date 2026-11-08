import logging
import time

logger = logging.getLogger('ggas.requisicao')


class LogRequisicaoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        inicio = time.perf_counter()
        try:
            response = self.get_response(request)
        except Exception:
            self._registrar(request, None, inicio)
            raise
        self._registrar(request, response, inicio)
        return response

    def _registrar(self, request, response, inicio):
        duracao_ms = int((time.perf_counter() - inicio) * 1000)
        status_code = getattr(response, 'status_code', 500)
        usuario = getattr(request, 'user', None)
        if usuario is not None and getattr(usuario, 'is_authenticated', False):
            quem = usuario.pk
        else:
            quem = '-'
        match = getattr(request, 'resolver_match', None)
        view = match.view_name if match else '-'
        if status_code >= 500:
            nivel = logging.ERROR
        elif status_code >= 400:
            nivel = logging.WARNING
        else:
            nivel = logging.INFO
        logger.log(
            nivel,
            '%s %s view=%s status=%s %sms usuario=%s ip=%s',
            request.method,
            request.path,
            view,
            status_code,
            duracao_ms,
            quem,
            request.META.get('REMOTE_ADDR') or '-',
        )
