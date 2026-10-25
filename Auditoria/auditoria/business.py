from decimal import Decimal

from AppCore.core.business.business import ModelInstanceBusiness

from .rules import RegistroAuditoriaRules


class RegistroAuditoriaBusiness(ModelInstanceBusiness):
    def registrar(self, acao, tipo_entidade, entidade_id, descricao, usuario, alteracoes=None):
        from .models import RegistroAuditoria

        dados = {
            'acao': (acao or '').strip(),
            'tipo_entidade': tipo_entidade,
            'entidade_id': str(entidade_id),
            'descricao': (descricao or '').strip(),
            'usuario': usuario,
            'alteracoes': self._sanear(alteracoes or {}),
        }
        RegistroAuditoriaRules().validar_novo(dados)
        return RegistroAuditoria.objects.create(
            acao=dados['acao'],
            tipo_entidade=dados['tipo_entidade'],
            entidade_id=dados['entidade_id'],
            descricao=dados['descricao'],
            usuario=usuario,
            nome_usuario=usuario.colaborador.nome,
            alteracoes=dados['alteracoes'],
        )

    def _sanear(self, valor):
        if isinstance(valor, dict):
            return {chave: self._sanear(item) for chave, item in valor.items()}
        if isinstance(valor, list):
            return [self._sanear(item) for item in valor]
        if isinstance(valor, Decimal):
            return str(valor)
        return valor
