import django_filters
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.filters import OrderingFilter

from AppCore.basics.mixins.mixins import AutenticadoMixin, PermissaoMixin
from AppCore.basics.views.basic_views import BasicGetAPIView, BasicListAPIView, BasicPostAPIView, BasicUpdateAPIView

from .models import Produto
from .serializers import ProdutoSerializer, ProdutoWriteSerializer


class ProdutoFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filtrar_q')

    class Meta:
        model = Produto
        fields = ['categoria', 'ativo', 'marca']

    def filtrar_q(self, queryset, nome, valor):
        texto = valor.strip()
        return queryset.filter(
            Q(nome__icontains=texto) | Q(marca__icontains=texto) | Q(codigo__icontains=texto)
        )


class ListarProdutosListView(AutenticadoMixin, BasicListAPIView):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ProdutoFilter
    ordering_fields = ['nome', 'codigo', 'preco_venda']
    success_message = 'Produtos listados.'

    @extend_schema(
        tags=['Produtos'],
        summary='Listar produtos',
        parameters=[
            OpenApiParameter(name='q', required=False, type=str),
            OpenApiParameter(name='categoria', required=False, type=str),
            OpenApiParameter(name='ativo', required=False, type=bool),
            OpenApiParameter(name='marca', required=False, type=str),
            OpenApiParameter(
                name='ordering',
                required=False,
                type=str,
                description='nome, codigo ou preco_venda. Use o sinal de menos para inverter.',
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CadastrarProdutoPostView(PermissaoMixin, BasicPostAPIView):
    permissao = 'gerir_produto'
    serializer_class = ProdutoWriteSerializer

    @extend_schema(tags=['Produtos'], summary='Cadastrar produto', request=ProdutoWriteSerializer)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def do_action_post(self, serializer, request, *args, **kwargs):
        produto = Produto.business_class().criar(serializer.validated_data, request.user)
        return {
            'status_code': 201,
            'message': 'Produto cadastrado.',
            'data': ProdutoSerializer(produto).data,
        }


class ObterProdutoGetView(AutenticadoMixin, BasicGetAPIView):
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    success_message = 'Produto encontrado.'

    @extend_schema(tags=['Produtos'], summary='Detalhar produto')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AtualizarProdutoUpdateView(PermissaoMixin, BasicUpdateAPIView):
    permissao = 'gerir_produto'
    queryset = Produto.objects.all()
    serializer_class = ProdutoWriteSerializer
    success_message = 'Produto atualizado.'

    @extend_schema(tags=['Produtos'], summary='Atualizar produto', request=ProdutoWriteSerializer)
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def do_action_patch(self, serializer, request, *args, **kwargs):
        produto = self.object.business.atualizar(serializer.validated_data, request.user)
        return {
            'message': 'Produto atualizado.',
            'data': ProdutoSerializer(produto).data,
        }
