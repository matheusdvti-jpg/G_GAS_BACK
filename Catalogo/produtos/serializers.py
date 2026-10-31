from rest_framework import serializers

from .choices import CATEGORIA_CHOICES
from .models import Produto


class ProdutoWriteSerializer(serializers.Serializer):
    codigo = serializers.CharField(max_length=40, required=False)
    nome = serializers.CharField(max_length=150, required=False)
    descricao = serializers.CharField(required=False, allow_blank=True)
    marca = serializers.CharField(max_length=80, required=False, allow_blank=True)
    categoria = serializers.ChoiceField(choices=CATEGORIA_CHOICES, required=False, allow_blank=True)
    preco_venda = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    preco_custo = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    saldo_cheio = serializers.IntegerField(required=False, min_value=0)
    saldo_seco = serializers.IntegerField(required=False, min_value=0)
    estoque_minimo = serializers.IntegerField(required=False, min_value=0)
    unidade = serializers.CharField(max_length=40, required=False, allow_blank=True)
    ativo = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if self.partial:
            return attrs
        obrigatorios = ('nome', 'descricao', 'preco_venda', 'preco_custo')
        ausentes = [campo for campo in obrigatorios if attrs.get(campo) in (None, '')]
        if ausentes:
            raise serializers.ValidationError(
                {campo: 'Este campo é obrigatório.' for campo in ausentes}
            )
        return attrs


class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = (
            'id',
            'codigo',
            'nome',
            'descricao',
            'marca',
            'categoria',
            'preco_venda',
            'preco_custo',
            'saldo_cheio',
            'saldo_seco',
            'estoque_minimo',
            'unidade',
            'ativo',
            'created_at',
            'updated_at',
        )
