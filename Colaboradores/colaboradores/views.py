from django.db.models import Count, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.filters import OrderingFilter

from AppCore.basics.mixins.mixins import AutenticadoMixin, PermissaoMixin
from AppCore.basics.views.basic_views import (
    BasicGetAPIView,
    BasicListAPIView,
    BasicPostAPIView,
    BasicUpdateAPIView,
)

from Pedidos.pedidos.choices import STATUS_ENTREGUE
from Pedidos.pedidos.models import Pedido

from .helpers import ColaboradorHelpers


def _contagem_entregas(status=None):
    consulta = Pedido.objects.filter(entregador=OuterRef('pk'))
    if status is not None:
        consulta = consulta.filter(status=status)
    return Coalesce(
        Subquery(
            consulta.order_by().values('entregador').annotate(total=Count('pk')).values('total')[:1],
            output_field=IntegerField(),
        ),
        0,
    )
from .models import Colaborador
from .serializers import ColaboradorSerializer, ColaboradorWriteSerializer, ContaWriteSerializer


class ListarColaboradoresListView(AutenticadoMixin, BasicListAPIView):
    queryset = Colaborador.objects.annotate(
        total_pedidos=_contagem_entregas(),
        pedidos_entregues=_contagem_entregas(STATUS_ENTREGUE),
    ).order_by('nome')
    serializer_class = ColaboradorSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        'perfil': ['exact'],
        'ativo': ['exact'],
        'nome': ['icontains'],
    }
    ordering_fields = ['nome', 'created_at']
    success_message = 'Colaboradores listados.'

    @extend_schema(
        tags=['Colaboradores'],
        summary='Listar colaboradores',
        parameters=[
            OpenApiParameter(name='perfil', required=False, type=str),
            OpenApiParameter(name='ativo', required=False, type=bool),
            OpenApiParameter(name='nome__icontains', required=False, type=str),
            OpenApiParameter(name='ordering', required=False, type=str),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CadastrarColaboradorPostView(PermissaoMixin, BasicPostAPIView):
    permissao = 'gestao_colaboradores'
    serializer_class = ColaboradorWriteSerializer
    success_message = 'Colaborador cadastrado.'

    @extend_schema(tags=['Colaboradores'], summary='Cadastrar colaborador', request=ColaboradorWriteSerializer)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer, request, *args, **kwargs):
        colaborador = Colaborador.business_class().criar(serializer.validated_data, request.user)
        return {
            'status_code': 201,
            'message': 'Colaborador cadastrado.',
            'data': ColaboradorSerializer(colaborador).data,
        }


class ObterColaboradorGetView(AutenticadoMixin, BasicGetAPIView):
    queryset = Colaborador.objects.all()
    serializer_class = ColaboradorSerializer
    success_message = 'Colaborador encontrado.'

    @extend_schema(tags=['Colaboradores'], summary='Detalhar colaborador')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AtualizarColaboradorUpdateView(PermissaoMixin, BasicUpdateAPIView):
    permissao = 'gestao_colaboradores'
    queryset = Colaborador.objects.all()
    serializer_class = ColaboradorWriteSerializer
    success_message = 'Colaborador atualizado.'

    @extend_schema(tags=['Colaboradores'], summary='Atualizar colaborador', request=ColaboradorWriteSerializer)
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def do_action_patch(self, serializer, request, *args, **kwargs):
        colaborador = self.object.business.atualizar(serializer.validated_data, request.user)
        return {
            'message': 'Colaborador atualizado.',
            'data': ColaboradorSerializer(colaborador).data,
        }


class CadastrarContaPostView(PermissaoMixin, BasicPostAPIView):
    permissao = 'gestao_colaboradores'
    queryset = Colaborador.objects.all()
    serializer_class = ContaWriteSerializer

    @extend_schema(tags=['Colaboradores'], summary='Criar conta de acesso do colaborador')
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer, request, *args, **kwargs):
        colaborador = ColaboradorHelpers().obter(kwargs['pk'])
        colaborador.business.criar_conta(serializer.validated_data, request.user)
        return {
            'status_code': 201,
            'message': 'Conta de acesso criada.',
            'data': ColaboradorSerializer(colaborador).data,
        }


class AtualizarContaUpdateView(PermissaoMixin, BasicUpdateAPIView):
    permissao = 'gestao_colaboradores'
    queryset = Colaborador.objects.all()
    serializer_class = ContaWriteSerializer
    success_message = 'Conta de acesso atualizada.'

    @extend_schema(tags=['Colaboradores'], summary='Atualizar conta de acesso do colaborador')
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def do_action_patch(self, serializer, request, *args, **kwargs):
        conta = self.object.business.atualizar_conta(serializer.validated_data, request.user)
        return {
            'message': 'Conta de acesso atualizada.',
            'data': conta.helper.resumo(),
        }
