import django_filters
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.filters import OrderingFilter

from AppCore.basics.mixins.mixins import AutenticadoMixin, PermissaoMixin
from AppCore.basics.views.basic_views import BasicGetAPIView, BasicListAPIView, BasicPostAPIView, BasicUpdateAPIView

from .helpers import PedidoHelpers
from .models import Pedido
from .serializers import PedidoSerializer, PedidoWriteSerializer, StatusPedidoSerializer


class PedidoFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filtrar_q')
    de = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    ate = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = Pedido
        fields = ['status', 'cliente', 'entregador']

    def filtrar_q(self, queryset, nome, valor):
        texto = valor.strip()
        digitos = ''.join(caractere for caractere in texto if caractere.isdigit())
        consulta = (
            Q(codigo__icontains=texto)
            | Q(nome_cliente__icontains=texto)
            | Q(telefone_cliente__icontains=texto)
            | Q(nome_entregador__icontains=texto)
            | Q(bairro__icontains=texto)
        )
        if digitos:
            consulta |= Q(telefone_cliente__icontains=digitos)
        return queryset.filter(consulta)


class PedidoQuerysetMixin:
    def get_queryset(self):
        return PedidoHelpers().para_consulta()


class ListarPedidosListView(PedidoQuerysetMixin, AutenticadoMixin, BasicListAPIView):
    serializer_class = PedidoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PedidoFilter
    ordering_fields = ['created_at', 'codigo', 'total']
    success_message = 'Pedidos listados.'

    @extend_schema(
        tags=['Pedidos'],
        summary='Listar pedidos',
        parameters=[
            OpenApiParameter(name='status', required=False, type=str),
            OpenApiParameter(name='cliente', required=False, type=int),
            OpenApiParameter(name='entregador', required=False, type=int),
            OpenApiParameter(
                name='q',
                required=False,
                type=str,
                description='Código, cliente, telefone, entregador ou bairro',
            ),
            OpenApiParameter(name='de', required=False, type=str, description='Data inicial AAAA-MM-DD'),
            OpenApiParameter(name='ate', required=False, type=str, description='Data final AAAA-MM-DD'),
            OpenApiParameter(
                name='ordering',
                required=False,
                type=str,
                description='created_at, codigo ou total. Use o sinal de menos para inverter.',
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CadastrarPedidoPostView(PermissaoMixin, BasicPostAPIView):
    permissao = 'nova_venda'
    serializer_class = PedidoWriteSerializer

    @extend_schema(tags=['Pedidos'], summary='Registrar venda', request=PedidoWriteSerializer)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer, request, *args, **kwargs):
        pedido = Pedido.business_class().criar(serializer.validated_data, request.user)
        return {
            'status_code': 201,
            'message': 'Pedido registrado.',
            'data': PedidoSerializer(pedido).data,
        }


class ObterPedidoGetView(PedidoQuerysetMixin, AutenticadoMixin, BasicGetAPIView):
    serializer_class = PedidoSerializer
    success_message = 'Pedido encontrado.'

    @extend_schema(tags=['Pedidos'], summary='Detalhar pedido')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AlterarStatusPedidoUpdateView(PedidoQuerysetMixin, AutenticadoMixin, BasicUpdateAPIView):
    serializer_class = StatusPedidoSerializer
    success_message = 'Status do pedido atualizado.'

    @extend_schema(tags=['Pedidos'], summary='Alterar status do pedido', request=StatusPedidoSerializer)
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def do_action_patch(self, serializer, request, *args, **kwargs):
        pedido = self.object.business.alterar_status(
            serializer.validated_data['status'],
            request.user,
            serializer.validated_data.get('observacao', ''),
        )
        return {
            'message': 'Status do pedido atualizado.',
            'data': PedidoSerializer(pedido).data,
        }
