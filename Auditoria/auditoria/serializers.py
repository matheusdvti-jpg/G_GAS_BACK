from rest_framework import serializers

from .models import RegistroAuditoria


class RegistroAuditoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroAuditoria
        fields = (
            'id',
            'acao',
            'tipo_entidade',
            'entidade_id',
            'descricao',
            'usuario',
            'nome_usuario',
            'alteracoes',
            'created_at',
        )
