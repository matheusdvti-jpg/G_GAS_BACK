from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from AppCore.basics.decorators.decorators import handle_exceptions
from AppCore.basics.mixins.mixins import AutenticadoMixin, PermissaoMixin

from .business import LeituraBusiness


class PainelGetView(AutenticadoMixin, APIView):
    @extend_schema(tags=['Relatórios'], summary='Painel operacional do dia')
    @handle_exceptions
    def get(self, request):
        return Response(
            {
                'status': 'success',
                'message': 'Painel carregado.',
                'data': LeituraBusiness().painel(),
            }
        )


class PeriodoGetView(PermissaoMixin, APIView):
    permissao = 'relatorios_financeiros'

    @extend_schema(
        tags=['Relatórios'],
        summary='Fechamento financeiro do período',
        parameters=[
            OpenApiParameter(name='de', required=False, type=str, description='Data inicial AAAA-MM-DD'),
            OpenApiParameter(name='ate', required=False, type=str, description='Data final AAAA-MM-DD'),
        ],
    )
    @handle_exceptions
    def get(self, request):
        return Response(
            {
                'status': 'success',
                'message': 'Relatório do período carregado.',
                'data': LeituraBusiness().periodo(
                    request.query_params.get('de'),
                    request.query_params.get('ate'),
                ),
            }
        )
