from AppCore.core.business.business import ModelInstanceBusiness


class ProdutoBusiness(ModelInstanceBusiness):
    CAMPOS = (
        'codigo',
        'nome',
        'descricao',
        'marca',
        'categoria',
        'preco_venda',
        'preco_custo',
        'saldo_cheio',
        'saldo_seco',
        'estoque_minimo',
        'unidade',
        'ativo',
    )

    def criar(self, dados, usuario):
        from .models import Produto

        Produto.rules_class().validar_novo(dados)
        produto = Produto.objects.create(**{campo: dados[campo] for campo in self.CAMPOS})
        self._auditar(usuario, 'CRIAR_PRODUTO', produto.id, f'Produto {produto.codigo} cadastrado.')
        return produto

    def atualizar(self, dados, usuario):
        from .helpers import ProdutoHelpers

        produto = ProdutoHelpers().bloquear(self.object_instance.pk)
        antes = {campo: getattr(produto, campo) for campo in self.CAMPOS}
        produto.rules.validar_atualizacao(dados)
        alterados = [campo for campo in self.CAMPOS if campo in dados]
        for campo in alterados:
            setattr(produto, campo, dados[campo])
        if alterados:
            produto.save(update_fields=[*alterados, 'updated_at'])
        self._auditar(
            usuario,
            'ATUALIZAR_PRODUTO',
            produto.id,
            f'Produto {produto.codigo} atualizado.',
            self._alteracoes(antes, produto),
        )
        return produto

    def _alteracoes(self, antes, produto):
        mudancas = {}
        for campo, valor_anterior in antes.items():
            valor_novo = getattr(produto, campo)
            if valor_anterior != valor_novo:
                mudancas[campo] = {'antes': valor_anterior, 'depois': valor_novo}
        return mudancas

    def _auditar(self, usuario, acao, entidade_id, descricao, alteracoes=None):
        from Auditoria.auditoria.business import RegistroAuditoriaBusiness

        RegistroAuditoriaBusiness().registrar(
            acao=acao,
            tipo_entidade='PRODUTO',
            entidade_id=entidade_id,
            descricao=descricao,
            usuario=usuario,
            alteracoes=alteracoes,
        )
