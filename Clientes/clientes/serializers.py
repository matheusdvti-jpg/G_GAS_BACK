from rest_framework import serializers

from .models import Cliente


class ClienteWriteSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150, required=False)
    telefone = serializers.CharField(max_length=20, required=False)
    telefone_secundario = serializers.CharField(max_length=20, required=False, allow_blank=True)
    logradouro = serializers.CharField(max_length=150, required=False)
    numero = serializers.CharField(max_length=20, required=False, allow_blank=True)
    complemento = serializers.CharField(max_length=80, required=False, allow_blank=True)
    bairro = serializers.CharField(max_length=80, required=False, allow_blank=True)
    cidade = serializers.CharField(max_length=80, required=False, allow_blank=True)
    ponto_referencia = serializers.CharField(max_length=150, required=False, allow_blank=True)
    observacoes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if self.partial:
            return attrs
        obrigatorios = ('nome', 'telefone', 'logradouro')
        ausentes = [campo for campo in obrigatorios if not attrs.get(campo)]
        if ausentes:
            raise serializers.ValidationError(
                {campo: 'Este campo é obrigatório.' for campo in ausentes}
            )
        return attrs


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = (
            'id',
            'nome',
            'telefone',
            'telefone_secundario',
            'logradouro',
            'numero',
            'complemento',
            'bairro',
            'cidade',
            'ponto_referencia',
            'observacoes',
            'total_pedidos',
            'total_gasto',
            'created_at',
            'updated_at',
        )
