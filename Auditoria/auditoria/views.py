import django_filters
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.filters import OrderingFilter

from AppCore.basics.mixins.mixins import PermissaoMixin
from AppCore.basics.views.basic_views import BasicGetAPIView, BasicListAPIView

from .helpers import RegistroAuditoriaHelpers
from .models import RegistroAuditoria
from .serializers import RegistroAuditoriaSerializer


class RegistroAuditoriaFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filtrar_q')

    class Meta:
        model = RegistroAuditoria
        fields = ['acao', 'tipo_entidade', 'entidade_id', 'usuario']

    def filtrar_q(self, queryset, nome, valor):
        texto = valor.strip()
        return queryset.filter(Q(descricao__icontains=texto) | Q(nome_usuario__icontains=texto))


class ListarAuditoriaListView(PermissaoMixin, BasicListAPIView):
    permissao = 'auditoria_sistema'
    serializer_class = RegistroAuditoriaSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = RegistroAuditoriaFilter
    ordering_fields = ['created_at', 'acao']
    success_message = 'Registros de auditoria listados.'

    def get_queryset(self):
        return RegistroAuditoriaHelpers().para_consulta()

    @extend_schema(
        tags=['Auditoria'],
        summary='Listar auditoria',
        parameters=[
            OpenApiParameter(name='acao', required=False, type=str),
            OpenApiParameter(name='tipo_entidade', required=False, type=str),
            OpenApiParameter(name='entidade_id', required=False, type=str),
            OpenApiParameter(name='usuario', required=False, type=int),
            OpenApiParameter(name='q', required=False, type=str),
            OpenApiParameter(
                name='ordering',
                required=False,
                type=str,
                description='created_at ou acao. Use o sinal de menos para inverter.',
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ObterAuditoriaGetView(PermissaoMixin, BasicGetAPIView):
    permissao = 'auditoria_sistema'
    serializer_class = RegistroAuditoriaSerializer
    success_message = 'Registro de auditoria encontrado.'

    def get_queryset(self):
        return RegistroAuditoriaHelpers().para_consulta()

    @extend_schema(tags=['Auditoria'], summary='Detalhar registro de auditoria')
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
