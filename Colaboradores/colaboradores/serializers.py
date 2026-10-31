from rest_framework import serializers

from .choices import PERFIL_CHOICES
from .models import Colaborador


class ContaWriteSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)


class ColaboradorWriteSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150, required=False)
    cpf = serializers.CharField(max_length=18, required=False)
    telefone = serializers.CharField(max_length=20, required=False)
    perfil = serializers.ChoiceField(choices=PERFIL_CHOICES, required=False)
    ativo = serializers.BooleanField(required=False)
    placa_veiculo = serializers.CharField(max_length=40, required=False, allow_blank=True)
    conta = ContaWriteSerializer(required=False)

    def validate(self, attrs):
        if self.partial:
            return attrs
        if attrs.get('perfil') == 'ENTREGADOR':
            obrigatorios = ('nome', 'telefone', 'perfil')
        else:
            obrigatorios = ('nome', 'cpf', 'telefone', 'perfil')
        ausentes = [campo for campo in obrigatorios if not attrs.get(campo)]
        if ausentes:
            raise serializers.ValidationError(
                {campo: 'Este campo é obrigatório.' for campo in ausentes}
            )
        return attrs


class ColaboradorSerializer(serializers.ModelSerializer):
    conta = serializers.SerializerMethodField()

    class Meta:
        model = Colaborador
        fields = (
            'id',
            'nome',
            'cpf',
            'telefone',
            'perfil',
            'ativo',
            'placa_veiculo',
            'conta',
            'created_at',
            'updated_at',
        )

    def get_conta(self, obj):
        conta = obj.helper.conta_ou_nenhuma()
        if conta is None:
            return None
        return conta.helper.resumo()
