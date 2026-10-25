from AppCore.core.business.business import ModelInstanceBusiness


class ClienteBusiness(ModelInstanceBusiness):
    CAMPOS = (
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
    )

    def criar(self, dados, usuario):
        from .models import Cliente

        self.object_instance = None
        Cliente.rules_class().validar_novo(dados)
        cliente = Cliente.objects.create(**{campo: dados.get(campo, '') for campo in self.CAMPOS})
        self._auditar(
            usuario,
            'CRIAR_CLIENTE',
            cliente.id,
            f'Cliente {cliente.nome} cadastrado.',
        )
        return cliente

    def atualizar(self, dados, usuario):
        antes = {campo: getattr(self.object_instance, campo) for campo in self.CAMPOS}
        self.object_instance.rules.validar_atualizacao(dados)
        for campo in self.CAMPOS:
            if campo in dados:
                setattr(self.object_instance, campo, dados[campo])
        self.object_instance.save()
        self._auditar(
            usuario,
            'ATUALIZAR_CLIENTE',
            self.object_instance.id,
            f'Cliente {self.object_instance.nome} atualizado.',
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
            tipo_entidade='CLIENTE',
            entidade_id=entidade_id,
            descricao=descricao,
            usuario=usuario,
            alteracoes=alteracoes,
        )
