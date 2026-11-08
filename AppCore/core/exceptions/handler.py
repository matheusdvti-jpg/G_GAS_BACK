import logging

from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    view = context.get('view')
    nome = type(view).__name__ if view is not None else '-'
    if response is None:
        logger.exception('Erro não tratado na view %s', nome)
        return None
    if response.status_code >= 500:
        logger.error('Erro %s na view %s: %s', response.status_code, nome, type(exc).__name__)
    elif response.status_code >= 400:
        logger.warning('Resposta %s na view %s: %s', response.status_code, nome, type(exc).__name__)

    detail = response.data.get('detail', response.data) if isinstance(response.data, dict) else response.data
    response.data = {
        'status': 'error',
        'detail': detail,
    }
    return response
