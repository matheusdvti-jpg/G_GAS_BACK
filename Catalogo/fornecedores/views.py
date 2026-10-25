import django_filters
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.filters import OrderingFilter

from AppCore.basics.mixins.mixins import AutenticadoMixin, PermissaoMixin
from AppCore.basics.views.basic_views import BasicGetAPIView, BasicListAPIView, BasicPostAPIView, BasicUpdateAPIView

from .models import Fornecedor
from .serializers import FornecedorSerializer, FornecedorWriteSerializer


class FornecedorFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filtrar_q')

    class Meta:
        model = Fornecedor
        fields = ['ativo', 'cidade']

    def filtrar_q(self, queryset, nome, valor):
        texto = valor.strip()
        digitos = ''.join(caractere for caractere in texto if caractere.isdigit())
        consulta = Q(nome_fantasia__icontains=texto) | Q(razao_social__icontains=texto) | Q(cnpj__icontains=texto)
        if digitos:
            consulta |= Q(cnpj__icontains=digitos) | Q(telefone__icontains=digitos)
        return queryset.filter(consulta)


class ListarFornecedoresListView(AutenticadoMixin, BasicListAPIView):
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = FornecedorFilter
    ordering_fields = ['nome_fantasia', 'created_at']
    success_message = 'Fornecedores listados.'

    @extend_schema(
        tags=['Fornecedores'],
        summary='Listar fornecedores',
        parameters=[
            OpenApiParameter(name='q', required=False, type=str),
            OpenApiParameter(name='ativo', required=False, type=bool),
            OpenApiParameter(name='cidade', required=False, type=str),
            OpenApiParameter(
                name='ordering',
                required=False,
                type=str,
                description='nome_fantasia ou created_at. Use o sinal de menos para inverter.',
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CadastrarFornecedorPostView(PermissaoMixin, BasicPostAPIView):
    permissao = 'gerir_fornecedor'
    serializer_class = FornecedorWriteSerializer

    @extend_schema(tags=['Fornecedores'], summary='Cadastrar fornecedor', request=FornecedorWriteSerializer)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer, request, *args, **kwargs):
        fornecedor = Fornecedor.business_class().criar(serializer.validated_data, request.user)
        return {
            'status_code': 201,
            'message': 'Fornecedor cadastrado.',
            'data': FornecedorSerializer(fornecedor).data,
        }


class ObterFornecedorGetView(AutenticadoMixin, BasicGetAPIView):
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer
    success_message = 'Fornecedor encontrado.'

    @extend_schema(tags=['Fornecedores'], summary='Detalhar fornecedor')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AtualizarFornecedorUpdateView(PermissaoMixin, BasicUpdateAPIView):
    permissao = 'gerir_fornecedor'
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorWriteSerializer
    success_message = 'Fornecedor atualizado.'

    @extend_schema(tags=['Fornecedores'], summary='Atualizar fornecedor', request=FornecedorWriteSerializer)
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def do_action_patch(self, serializer, request, *args, **kwargs):
        fornecedor = self.object.business.atualizar(serializer.validated_data, request.user)
        return {
            'message': 'Fornecedor atualizado.',
            'data': FornecedorSerializer(fornecedor).data,
        }
