from rest_framework import serializers

from .choices import FORMA_PAGAMENTO_CHOICES, STATUS_PEDIDO_CHOICES, TIPO_DESCONTO_CHOICES
from .models import HistoricoStatusPedido, ItemPedido, Pedido


class ItemPedidoWriteSerializer(serializers.Serializer):
    produto_id = serializers.IntegerField()
    quantidade = serializers.IntegerField(min_value=1)
    vazios_recebidos = serializers.IntegerField(required=False, min_value=0)


class PedidoWriteSerializer(serializers.Serializer):
    cliente_id = serializers.IntegerField()
    entregador_id = serializers.IntegerField()
    itens = ItemPedidoWriteSerializer(many=True)
    tipo_desconto = serializers.ChoiceField(choices=TIPO_DESCONTO_CHOICES, required=False)
    valor_desconto = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
    )
    forma_pagamento = serializers.ChoiceField(choices=FORMA_PAGAMENTO_CHOICES)
    valor_recebido = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
    )
    observacoes = serializers.CharField(required=False, allow_blank=True)


class StatusPedidoSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=STATUS_PEDIDO_CHOICES)
    observacao = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if 'status' not in attrs:
            raise serializers.ValidationError({'status': 'Informe o status.'})
        return attrs


class ItemPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPedido
        fields = (
            'id',
            'produto',
            'nome_produto',
            'marca',
            'preco_unitario',
            'quantidade',
            'total',
            'vazios_recebidos',
            'nome_vazio',
        )


class HistoricoStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricoStatusPedido
        fields = ('id', 'status', 'usuario', 'nome_usuario', 'observacao', 'created_at')


class PedidoSerializer(serializers.ModelSerializer):
    itens = ItemPedidoSerializer(many=True, read_only=True)
    historico = HistoricoStatusSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = (
            'id',
            'codigo',
            'cliente',
            'nome_cliente',
            'telefone_cliente',
            'logradouro',
            'numero',
            'complemento',
            'bairro',
            'cidade',
            'ponto_referencia',
            'itens',
            'subtotal',
            'tipo_desconto',
            'valor_desconto',
            'total',
            'forma_pagamento',
            'valor_recebido',
            'troco',
            'entregador',
            'nome_entregador',
            'status',
            'historico',
            'observacoes',
            'criado_por',
            'nome_criado_por',
            'created_at',
            'updated_at',
        )
