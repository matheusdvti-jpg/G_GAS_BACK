from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from AppCore.common.texts.messages import CREDENCIAIS_INVALIDAS
from AppCore.core.exceptions.exceptions import BusinessRuleException

from Colaboradores.colaboradores.helpers import UserHelpers


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        identificador = (attrs.get(self.username_field) or '').strip()
        senha = attrs.get('password')
        usuario = UserHelpers().buscar_por_identificador(identificador)
        if usuario is None or not usuario.check_password(senha):
            raise serializers.ValidationError({'detail': CREDENCIAIS_INVALIDAS})

        try:
            usuario.rules.pode_autenticar()
        except BusinessRuleException as exc:
            raise serializers.ValidationError({'detail': exc.message})

        attrs[self.username_field] = usuario.get_username()
        data = super().validate(attrs)
        data['usuario'] = usuario.helper.resumo()
        return data
