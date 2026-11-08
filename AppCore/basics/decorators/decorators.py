import logging
from functools import wraps

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from AppCore.common.texts.messages import (
    RESPONSE_ALGO_QUE_MANDOU_ESTA_ERRADO,
    RESPONSE_ALGUM_DADO_NAO_FOI_ENCONTRADO,
    RESPONSE_ERRO_INTERNO_SERVIDOR,
    RESPONSE_TENTE_NOVAMENTE,
    RESPONSE_VOCE_NAO_PODE_FAZER_ISSO,
)
from AppCore.core.exceptions.exceptions import (
    AuthorizationException,
    BusinessRuleException,
    NotFoundException,
    SystemErrorException,
    ValidationException,
)

logger = logging.getLogger(__name__)


def _resumo(err):
    texto = str(err).replace('\n', ' ')
    if len(texto) > 300:
        return texto[:300] + '...'
    return texto


def handle_exceptions(func):
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        try:
            return func(self, request, *args, **kwargs)
        except BusinessRuleException as err:
            logger.warning('Regra de negócio recusada em %s: %s', func.__qualname__, _resumo(err))
            return Response(
                {
                    'status': 'error',
                    'detail': str(err) or RESPONSE_TENTE_NOVAMENTE,
                    'details': getattr(err, 'details', {}),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValidationException as err:
            logger.warning('Validação recusada em %s: %s', func.__qualname__, _resumo(err))
            return Response(
                {
                    'status': 'error',
                    'detail': str(err) or RESPONSE_ALGO_QUE_MANDOU_ESTA_ERRADO,
                    'details': getattr(err, 'details', {}),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DRFValidationError as err:
            logger.warning('Validação recusada em %s: %s', func.__qualname__, _resumo(err))
            return Response(
                {'status': 'error', 'detail': err.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except (AuthorizationException, PermissionDenied) as err:
            logger.warning('Acesso negado em %s: %s', func.__qualname__, _resumo(err))
            return Response(
                {
                    'status': 'error',
                    'detail': str(err) or RESPONSE_VOCE_NAO_PODE_FAZER_ISSO,
                    'details': getattr(err, 'details', {}),
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        except NotFoundException as err:
            logger.info('Registro não encontrado em %s: %s', func.__qualname__, _resumo(err))
            return Response(
                {
                    'status': 'error',
                    'detail': str(err) or RESPONSE_ALGUM_DADO_NAO_FOI_ENCONTRADO,
                    'details': getattr(err, 'details', {}),
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except SystemErrorException as err:
            logger.exception('Erro interno do sistema na view: %s', err)
            return Response(
                {'status': 'error', 'detail': RESPONSE_ERRO_INTERNO_SERVIDOR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as err:
            logger.exception('Erro inesperado na view: %s', err)
            return Response(
                {'status': 'error', 'detail': RESPONSE_ERRO_INTERNO_SERVIDOR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return wrapper
