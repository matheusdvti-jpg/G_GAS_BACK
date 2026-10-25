import django_filters
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.filters import OrderingFilter

from AppCore.basics.mixins.mixins import AutenticadoMixin, PermissaoMixin
from AppCore.basics.views.basic_views import BasicGetAPIView, BasicListAPIView, BasicPostAPIView, BasicUpdateAPIView

from .models import Cliente
from .serializers import ClienteSerializer, ClienteWriteSerializer


class ClienteFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filtrar_q')

    class Meta:
        model = Cliente
        fields = ['cidade']

    def filtrar_q(self, queryset, nome, valor):
        texto = valor.strip()
        digitos = ''.join(caractere for caractere in texto if caractere.isdigit())
        consulta = (
            Q(nome__icontains=texto)
            | Q(telefone__icontains=texto)
            | Q(telefone_secundario__icontains=texto)
        )
        if digitos:
            consulta |= Q(telefone__icontains=digitos) | Q(telefone_secundario__icontains=digitos)
        return queryset.filter(consulta)


class ListarClientesListView(AutenticadoMixin, BasicListAPIView):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ClienteFilter
    ordering_fields = ['nome', 'created_at']
    success_message = 'Clientes listados.'

    @extend_schema(
        tags=['Clientes'],
        summary='Listar clientes',
        parameters=[
            OpenApiParameter(name='q', required=False, type=str, description='Nome ou telefone'),
            OpenApiParameter(name='cidade', required=False, type=str),
            OpenApiParameter(name='ordering', required=False, type=str),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CadastrarClientePostView(PermissaoMixin, BasicPostAPIView):
    permissao = 'cadastrar_cliente'
    serializer_class = ClienteWriteSerializer

    @extend_schema(tags=['Clientes'], summary='Cadastrar cliente', request=ClienteWriteSerializer)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer, request, *args, **kwargs):
        cliente = Cliente.business_class().criar(serializer.validated_data, request.user)
        return {
            'status_code': 201,
            'message': 'Cliente cadastrado.',
            'data': ClienteSerializer(cliente).data,
        }


class ObterClienteGetView(AutenticadoMixin, BasicGetAPIView):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    success_message = 'Cliente encontrado.'

    @extend_schema(tags=['Clientes'], summary='Detalhar cliente')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AtualizarClienteUpdateView(PermissaoMixin, BasicUpdateAPIView):
    permissao = 'cadastrar_cliente'
    queryset = Cliente.objects.all()
    serializer_class = ClienteWriteSerializer
    success_message = 'Cliente atualizado.'

    @extend_schema(tags=['Clientes'], summary='Atualizar cliente', request=ClienteWriteSerializer)
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def do_action_patch(self, serializer, request, *args, **kwargs):
        cliente = self.object.business.atualizar(serializer.validated_data, request.user)
        return {
            'message': 'Cliente atualizado.',
            'data': ClienteSerializer(cliente).data,
        }
