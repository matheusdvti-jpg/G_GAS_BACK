import logging

from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.mixins.mixins import AllowAnyMixin, AutenticadoMixin
from AppCore.common.texts.messages import CREDENCIAIS_INVALIDAS
from AppCore.core.exceptions.exceptions import BusinessRuleException

from Colaboradores.colaboradores.helpers import UserHelpers

from .bloqueio import bloqueado_ate, chave_de, limpar, registrar_falha
from .models import Sessao

logger = logging.getLogger(__name__)


def _ip(request) -> str:
    return request.META.get('REMOTE_ADDR') or '0.0.0.0'


def _samesite() -> str:
    # O painel na Vercel e a API no PythonAnywhere são sites diferentes.
    # Strict faz o navegador ignorar o cookie e a sessão cair na hora.
    if settings.SESSAO_COOKIE_SECURE:
        return 'None'
    return 'Lax'


def _particionar(response) -> None:
    if not settings.SESSAO_COOKIE_SECURE:
        return
    from http.cookies import Morsel

    if 'partitioned' not in Morsel._reserved:
        Morsel._reserved['partitioned'] = 'Partitioned'
        Morsel._flags.add('partitioned')
    response.cookies[settings.SESSAO_COOKIE_NAME]['partitioned'] = True


def _gravar_cookie(response, segredo: str) -> None:
    response.set_cookie(
        settings.SESSAO_COOKIE_NAME,
        segredo,
        max_age=settings.SESSAO_COOKIE_AGE,
        httponly=True,
        secure=settings.SESSAO_COOKIE_SECURE,
        samesite=_samesite(),
        path='/',
    )
    _particionar(response)


def _apagar_cookie(response) -> None:
    response.set_cookie(
        settings.SESSAO_COOKIE_NAME,
        '',
        max_age=0,
        expires='Thu, 01 Jan 1970 00:00:00 GMT',
        path='/',
        secure=settings.SESSAO_COOKIE_SECURE,
        httponly=True,
        samesite=_samesite(),
    )
    _particionar(response)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfView(AllowAnyMixin, APIView):
    @extend_schema(tags=['Auth'], summary='Entrega o token CSRF para o painel')
    def get(self, request):
        return Response({'csrfToken': get_token(request)})


@extend_schema(tags=['Auth'], summary='Autenticar e abrir sessão opaca')
class TokenObtainPairViewDOC(AllowAnyMixin, APIView):
    @handle_exceptions
    def post(self, request, *args, **kwargs):
        identificador = (request.data.get('username') or '').strip()
        senha = request.data.get('password') or ''
        ip = _ip(request)
        chave = chave_de(ip, identificador)
        if bloqueado_ate(chave):
            logger.warning('Login bloqueado por excesso de tentativas. identificador=%s ip=%s', identificador, ip)
            return Response(
                {'status': 'error', 'detail': 'Muitas tentativas de login. Aguarde 15 minutos.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        usuario = UserHelpers().buscar_por_identificador(identificador)
        if usuario is None or not usuario.check_password(senha):
            registrar_falha(chave)
            logger.warning('Login recusado. identificador=%s ip=%s', identificador, ip)
            raise serializers.ValidationError({'detail': CREDENCIAIS_INVALIDAS})
        try:
            usuario.rules.pode_autenticar()
        except BusinessRuleException as exc:
            registrar_falha(chave)
            logger.warning('Login recusado. identificador=%s ip=%s motivo=%s', identificador, ip, exc.message)
            raise serializers.ValidationError({'detail': exc.message})

        limpar(chave)
        segredo = Sessao.abrir(usuario)
        logger.info('Login aceito. usuario=%s ip=%s', usuario.pk, ip)
        response = Response({'usuario': usuario.helper.resumo()})
        _gravar_cookie(response, segredo)
        return response


@extend_schema(tags=['Auth'], summary='A sessão opaca não se renova por token')
class TokenRefreshViewDOC(AllowAnyMixin, APIView):
    def post(self, request, *args, **kwargs):
        return Response(
            {'detail': 'A sessão não usa token renovável.'},
            status=status.HTTP_410_GONE,
        )


@extend_schema(tags=['Auth'], summary='A sessão opaca não se verifica por token')
class TokenVerifyViewDOC(AllowAnyMixin, APIView):
    def post(self, request, *args, **kwargs):
        return Response(
            {'detail': 'A sessão não usa token verificável.'},
            status=status.HTTP_410_GONE,
        )


class EuView(AutenticadoMixin, APIView):
    @extend_schema(tags=['Auth'], summary='Dados do usuário autenticado')
    @handle_exceptions
    def get(self, request):
        return Response(
            {
                'status': 'success',
                'message': 'Sessão ativa.',
                'data': request.user.helper.resumo(),
            }
        )


class SairView(AllowAnyMixin, APIView):
    @extend_schema(tags=['Auth'], summary='Encerrar a sessão atual')
    def post(self, request):
        segredo = request.COOKIES.get(settings.SESSAO_COOKIE_NAME)
        if segredo:
            Sessao.revogar_segredo(segredo)
        response = Response({'status': 'success', 'message': 'Sessão encerrada.'})
        _apagar_cookie(response)
        return response
