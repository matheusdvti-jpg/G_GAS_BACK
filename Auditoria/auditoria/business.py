from decimal import Decimal

from AppCore.core.business.business import ModelInstanceBusiness

from .rules import RegistroAuditoriaRules

CAMPOS_OCULTOS = {
    'password',
    'senha',
    'hash',
    'cookie',
    'csrftoken',
    'ggas_sessao',
    'chave_hash',
}


class RegistroAuditoriaBusiness(ModelInstanceBusiness):
    def registrar(self, acao, tipo_entidade, entidade_id, descricao, usuario, alteracoes=None, nome_usuario=''):
        from .models import RegistroAuditoria

        if usuario is not None:
            nome = usuario.colaborador.nome
        else:
            nome = (nome_usuario or '').strip()
        dados = {
            'acao': (acao or '').strip(),
            'tipo_entidade': tipo_entidade,
            'entidade_id': str(entidade_id),
            'descricao': (descricao or '').strip(),
            'usuario': usuario,
            'nome_usuario': nome,
            'alteracoes': self._sanear(alteracoes or {}),
        }
        RegistroAuditoriaRules().validar_novo(dados)
        return RegistroAuditoria.objects.create(
            acao=dados['acao'],
            tipo_entidade=dados['tipo_entidade'],
            entidade_id=dados['entidade_id'],
            descricao=dados['descricao'],
            usuario=usuario,
            nome_usuario=nome[:150],
            alteracoes=dados['alteracoes'],
        )

    def _sanear(self, valor):
        if isinstance(valor, dict):
            return {
                chave: self._sanear(item)
                for chave, item in valor.items()
                if chave.lower() not in CAMPOS_OCULTOS
            }
        if isinstance(valor, list):
            return [self._sanear(item) for item in valor]
        if isinstance(valor, Decimal):
            return str(valor)
        return valor
