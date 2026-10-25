from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.mixins.mixins import AutenticadoMixin

from .serializers import CustomTokenObtainPairSerializer


@extend_schema(
    tags=['Auth'],
    summary='Autenticar com usuário ou e-mail e obter JWT',
)
class TokenObtainPairViewDOC(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(tags=['Auth'], summary='Renovar o access token')
class TokenRefreshViewDOC(TokenRefreshView):
    pass


@extend_schema(tags=['Auth'], summary='Verificar se um token JWT é válido')
class TokenVerifyViewDOC(TokenVerifyView):
    pass


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
