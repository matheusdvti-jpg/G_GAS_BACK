import django_filters
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.filters import OrderingFilter

from AppCore.basics.mixins.mixins import AutenticadoMixin, PermissaoMixin
from AppCore.basics.views.basic_views import BasicListAPIView, BasicPostAPIView

from .helpers import MovimentacaoHelpers
from .models import MovimentacaoEstoque
from .serializers import (
    ConferenciaEstoqueSerializer,
    EntradaEstoqueSerializer,
    MovimentacaoSerializer,
    SaidaEstoqueSerializer,
)


class MovimentacaoFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filtrar_q')

    class Meta:
        model = MovimentacaoEstoque
        fields = ['produto', 'tipo', 'tipo_saldo', 'pedido_id', 'fornecedor', 'cliente']

    def filtrar_q(self, queryset, nome, valor):
        texto = valor.strip()
        return queryset.filter(
            Q(nome_produto__icontains=texto)
            | Q(motivo__icontains=texto)
            | Q(nome_fornecedor__icontains=texto)
            | Q(codigo_pedido__icontains=texto)
        )


class ListarMovimentacoesListView(AutenticadoMixin, BasicListAPIView):
    serializer_class = MovimentacaoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = MovimentacaoFilter
    ordering_fields = ['created_at']
    success_message = 'Movimentações listadas.'

    def get_queryset(self):
        return MovimentacaoHelpers().para_consulta()

    @extend_schema(
        tags=['Estoque'],
        summary='Listar movimentações de estoque',
        parameters=[
            OpenApiParameter(
                name='q',
                required=False,
                type=str,
                description='Produto, motivo, fornecedor ou código do pedido',
            ),
            OpenApiParameter(name='produto', required=False, type=int),
            OpenApiParameter(name='tipo', required=False, type=str),
            OpenApiParameter(name='tipo_saldo', required=False, type=str),
            OpenApiParameter(name='pedido_id', required=False, type=int),
            OpenApiParameter(name='fornecedor', required=False, type=int),
            OpenApiParameter(name='cliente', required=False, type=int),
            OpenApiParameter(name='ordering', required=False, type=str, description='created_at'),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RegistrarEntradaPostView(PermissaoMixin, BasicPostAPIView):
    permissao = 'entrada_estoque'
    serializer_class = EntradaEstoqueSerializer

    @extend_schema(tags=['Estoque'], summary='Registrar entrada de fornecedor')
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer, request, *args, **kwargs):
        dados = serializer.validated_data
        movimentacao = MovimentacaoEstoque.business_class().registrar_entrada(
            produto_id=dados['produto_id'],
            fornecedor_id=dados['fornecedor_id'],
            quantidade=dados['quantidade'],
            custo_unitario=dados['custo_unitario'],
            usuario=request.user,
            motivo=dados.get('motivo', ''),
        )
        return {
            'status_code': 201,
            'message': 'Entrada de estoque registrada.',
            'data': MovimentacaoSerializer(movimentacao).data,
        }


class RegistrarSaidaPostView(PermissaoMixin, BasicPostAPIView):
    permissao = 'saida_manual_estoque'
    serializer_class = SaidaEstoqueSerializer

    @extend_schema(tags=['Estoque'], summary='Registrar saída manual')
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer, request, *args, **kwargs):
        dados = serializer.validated_data
        movimentacao = MovimentacaoEstoque.business_class().registrar_saida_manual(
            produto_id=dados['produto_id'],
            quantidade=dados['quantidade'],
            tipo=dados['tipo'],
            motivo=dados.get('motivo', ''),
            usuario=request.user,
            cliente_id=dados.get('cliente_id'),
        )
        return {
            'status_code': 201,
            'message': 'Saída de estoque registrada.',
            'data': MovimentacaoSerializer(movimentacao).data,
        }


class RegistrarConferenciaPostView(PermissaoMixin, BasicPostAPIView):
    permissao = 'conferencia_inventario'
    serializer_class = ConferenciaEstoqueSerializer

    @extend_schema(tags=['Estoque'], summary='Registrar conferência física')
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer, request, *args, **kwargs):
        dados = serializer.validated_data
        movimentacao = MovimentacaoEstoque.business_class().ajustar_inventario(
            produto_id=dados['produto_id'],
            contagem=dados['contagem'],
            motivo=dados['motivo'],
            usuario=request.user,
        )
        return {
            'status_code': 201,
            'message': 'Conferência de estoque registrada.',
            'data': MovimentacaoSerializer(movimentacao).data,
        }
