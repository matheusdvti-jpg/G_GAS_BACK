from AppCore.core.rules.rules import ModelInstanceRules

from .choices import TIPO_ENTIDADE_CHOICES


class RegistroAuditoriaRules(ModelInstanceRules):
    def validar_novo(self, dados):
        if not (dados.get('acao') or '').strip():
            self.return_exception('A ação da auditoria é obrigatória.')
        if not (dados.get('descricao') or '').strip():
            self.return_exception('A descrição da auditoria é obrigatória.')
        tipos = {codigo for codigo, _rotulo in TIPO_ENTIDADE_CHOICES}
        if dados.get('tipo_entidade') not in tipos:
            self.return_exception('Tipo de entidade inválido para auditoria.')
        if dados.get('usuario') is None:
            self.return_exception('A auditoria precisa identificar quem executou a ação.')
        return True
