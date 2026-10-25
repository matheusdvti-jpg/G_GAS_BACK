from AppCore.core.business.business import ModelInstanceBusiness


class FornecedorBusiness(ModelInstanceBusiness):
    CAMPOS = (
        'nome_fantasia',
        'razao_social',
        'cnpj',
        'telefone',
        'nome_contato',
        'endereco',
        'cidade',
        'produtos_fornecidos',
        'ativo',
    )

    def criar(self, dados, usuario):
        from .models import Fornecedor

        Fornecedor.rules_class().validar_novo(dados)
        fornecedor = Fornecedor.objects.create(**{campo: dados[campo] for campo in self.CAMPOS})
        self._auditar(
            usuario,
            'CRIAR_FORNECEDOR',
            fornecedor.id,
            f'Fornecedor {fornecedor.nome_fantasia} cadastrado.',
        )
        return fornecedor

    def atualizar(self, dados, usuario):
        antes = {campo: getattr(self.object_instance, campo) for campo in self.CAMPOS}
        self.object_instance.rules.validar_atualizacao(dados)
        for campo in self.CAMPOS:
            if campo in dados:
                setattr(self.object_instance, campo, dados[campo])
        self.object_instance.save()
        self._auditar(
            usuario,
            'ATUALIZAR_FORNECEDOR',
            self.object_instance.id,
            f'Fornecedor {self.object_instance.nome_fantasia} atualizado.',
            self._alteracoes(antes),
        )
        return self.object_instance

    def _alteracoes(self, antes):
        mudancas = {}
        for campo, valor_anterior in antes.items():
            valor_novo = getattr(self.object_instance, campo)
            if valor_anterior != valor_novo:
                mudancas[campo] = {'antes': valor_anterior, 'depois': valor_novo}
        return mudancas

    def _auditar(self, usuario, acao, entidade_id, descricao, alteracoes=None):
        from Auditoria.auditoria.business import RegistroAuditoriaBusiness

        RegistroAuditoriaBusiness().registrar(
            acao=acao,
            tipo_entidade='FORNECEDOR',
            entidade_id=entidade_id,
            descricao=descricao,
            usuario=usuario,
            alteracoes=alteracoes,
        )
