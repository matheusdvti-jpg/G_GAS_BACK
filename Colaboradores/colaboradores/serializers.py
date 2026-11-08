from rest_framework import serializers

from .choices import PERFIL_CHOICES
from .models import Colaborador
from .permissoes import usuario_pode


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
    total_pedidos = serializers.SerializerMethodField()
    pedidos_entregues = serializers.SerializerMethodField()

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
            'total_pedidos',
            'pedidos_entregues',
            'created_at',
            'updated_at',
        )

    def get_total_pedidos(self, obj):
        anotado = getattr(obj, 'total_pedidos', None)
        if isinstance(anotado, int):
            return anotado
        return obj.entregas.count()

    def get_pedidos_entregues(self, obj):
        anotado = getattr(obj, 'pedidos_entregues', None)
        if isinstance(anotado, int):
            return anotado
        return obj.entregas.filter(status='ENTREGUE').count()

    def get_conta(self, obj):
        conta = obj.helper.conta_ou_nenhuma()
        if conta is None:
            return None
        return conta.helper.resumo()

    def to_representation(self, instance):
        dados = super().to_representation(instance)
        request = self.context.get('request')
        usuario = getattr(request, 'user', None) if request is not None else None
        if (
            usuario is not None
            and getattr(usuario, 'is_authenticated', False)
            and not usuario_pode(usuario, 'ver_dados_colaborador')
        ):
            dados.pop('cpf', None)
            dados.pop('conta', None)
        return dados
