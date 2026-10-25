from rest_framework import serializers

from .choices import TIPOS_SAIDA_MANUAL
from .models import MovimentacaoEstoque


class EntradaEstoqueSerializer(serializers.Serializer):
    produto_id = serializers.IntegerField()
    fornecedor_id = serializers.IntegerField()
    quantidade = serializers.IntegerField(min_value=1)
    custo_unitario = serializers.DecimalField(max_digits=10, decimal_places=2)
    motivo = serializers.CharField(required=False, allow_blank=True)


class SaidaEstoqueSerializer(serializers.Serializer):
    produto_id = serializers.IntegerField()
    quantidade = serializers.IntegerField(min_value=1)
    tipo = serializers.ChoiceField(choices=[(tipo, tipo) for tipo in TIPOS_SAIDA_MANUAL])
    motivo = serializers.CharField(required=False, allow_blank=True)
    cliente_id = serializers.IntegerField(required=False)


class ConferenciaEstoqueSerializer(serializers.Serializer):
    produto_id = serializers.IntegerField()
    contagem = serializers.IntegerField(min_value=0)
    motivo = serializers.CharField()


class MovimentacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimentacaoEstoque
        fields = (
            'id',
            'produto',
            'nome_produto',
            'tipo',
            'tipo_saldo',
            'quantidade',
            'saldo_anterior',
            'saldo_novo',
            'custo_unitario',
            'fornecedor',
            'nome_fornecedor',
            'cliente',
            'nome_cliente',
            'pedido_id',
            'codigo_pedido',
            'motivo',
            'usuario',
            'nome_usuario',
            'created_at',
        )
