from rest_framework import serializers

from .models import Fornecedor


class FornecedorWriteSerializer(serializers.Serializer):
    nome_fantasia = serializers.CharField(max_length=150, required=False)
    razao_social = serializers.CharField(max_length=150, required=False)
    cnpj = serializers.CharField(max_length=18, required=False)
    telefone = serializers.CharField(max_length=20, required=False)
    nome_contato = serializers.CharField(max_length=150, required=False)
    endereco = serializers.CharField(max_length=200, required=False)
    cidade = serializers.CharField(max_length=80, required=False)
    produtos_fornecidos = serializers.ListField(
        child=serializers.CharField(max_length=150),
        required=False,
        allow_empty=True,
    )
    ativo = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if self.partial:
            return attrs
        obrigatorios = (
            'nome_fantasia',
            'razao_social',
            'cnpj',
            'telefone',
            'nome_contato',
            'endereco',
            'cidade',
        )
        ausentes = [campo for campo in obrigatorios if not attrs.get(campo)]
        if ausentes:
            raise serializers.ValidationError(
                {campo: 'Este campo é obrigatório.' for campo in ausentes}
            )
        return attrs


class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = (
            'id',
            'nome_fantasia',
            'razao_social',
            'cnpj',
            'telefone',
            'nome_contato',
            'endereco',
            'cidade',
            'produtos_fornecidos',
            'ativo',
            'created_at',
            'updated_at',
        )
