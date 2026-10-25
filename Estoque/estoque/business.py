from AppCore.core.business.business import ModelInstanceBusiness

from .choices import (
    SALDO_CHEIO,
    SALDO_SECO,
    TIPO_AJUSTE_INVENTARIO,
    TIPO_ENTRADA_FORNECEDOR,
    TIPO_ENTRADA_VAZIO,
    TIPO_ESTORNO_CANCELAMENTO,
    TIPO_SAIDA_VAZIO,
    TIPO_SAIDA_VENDA,
)
from .helpers import MovimentacaoHelpers
from .rules import MovimentacaoRules


class MovimentacaoBusiness(ModelInstanceBusiness):
    def registrar_entrada(self, produto_id, fornecedor_id, quantidade, custo_unitario, usuario, motivo=''):
        from Catalogo.fornecedores.models import Fornecedor
        from Catalogo.produtos.models import Produto

        produto = MovimentacaoHelpers().obter(Produto, produto_id, 'Produto não encontrado.')
        fornecedor = MovimentacaoHelpers().obter(Fornecedor, fornecedor_id, 'Fornecedor não encontrado.')
        MovimentacaoRules().validar_fornecedor_da_carga(fornecedor)
        custo = MovimentacaoRules().validar_entrada(quantidade, custo_unitario)
        movimentacao = self._aplicar(
            produto_id=produto.id,
            tipo=TIPO_ENTRADA_FORNECEDOR,
            tipo_saldo=SALDO_CHEIO,
            quantidade=quantidade,
            usuario=usuario,
            motivo=(motivo or '').strip(),
            custo_unitario=custo,
            fornecedor=fornecedor,
        )
        self._auditar(
            usuario,
            'ENTRADA_ESTOQUE',
            produto.id,
            (
                f'Entrada de {quantidade} un de {produto.nome} '
                f'(Fornecedor: {fornecedor.nome_fantasia}). '
                f'Saldo anterior: {movimentacao.saldo_anterior} -> Novo: {movimentacao.saldo_novo}'
            ),
        )
        return movimentacao

    def registrar_saida_manual(self, produto_id, quantidade, tipo, motivo, usuario, cliente_id=None):
        from Catalogo.produtos.models import Produto
        from Clientes.clientes.models import Cliente

        produto = MovimentacaoHelpers().obter(Produto, produto_id, 'Produto não encontrado.')
        cliente = None
        if cliente_id is not None:
            cliente = MovimentacaoHelpers().obter(Cliente, cliente_id, 'Cliente não encontrado.')
        texto = MovimentacaoRules().validar_saida_manual(tipo, quantidade, motivo, cliente)
        movimentacao = self._aplicar(
            produto_id=produto.id,
            tipo=tipo,
            tipo_saldo=SALDO_CHEIO,
            quantidade=-quantidade,
            usuario=usuario,
            motivo=texto,
            cliente=cliente,
        )
        destino = f' para {cliente.nome}' if cliente is not None else ''
        self._auditar(
            usuario,
            'SAIDA_MANUAL_ESTOQUE',
            produto.id,
            f'Saída manual de {quantidade} un de {produto.nome} ({tipo}){destino}. Motivo: {texto}',
        )
        return movimentacao

    def ajustar_inventario(self, produto_id, contagem, motivo, usuario):
        from Catalogo.produtos.models import Produto

        produto = MovimentacaoHelpers().obter(Produto, produto_id, 'Produto não encontrado.')
        texto = MovimentacaoRules().validar_conferencia(contagem, motivo)
        bloqueado = MovimentacaoHelpers().bloquear_produto(produto.id)
        diferenca = contagem - bloqueado.saldo_cheio
        sinal = '+' if diferenca > 0 else ''
        motivo_completo = (
            f'Ajuste de inventário físico. Diferença: {sinal}{diferenca}. Motivo: {texto}'
        )
        movimentacao = self._aplicar(
            produto_id=produto.id,
            tipo=TIPO_AJUSTE_INVENTARIO,
            tipo_saldo=SALDO_CHEIO,
            quantidade=diferenca,
            usuario=usuario,
            motivo=motivo_completo,
            produto_bloqueado=bloqueado,
        )
        self._auditar(
            usuario,
            'AJUSTE_INVENTARIO',
            produto.id,
            (
                f'Conferência de estoque para {produto.nome}: '
                f'contagem física {contagem} (era {movimentacao.saldo_anterior}). Motivo: {texto}'
            ),
        )
        return movimentacao

    def registrar_saida_venda(self, produto, quantidade, usuario, pedido_id, codigo_pedido):
        return self._aplicar(
            produto_id=produto.id,
            tipo=TIPO_SAIDA_VENDA,
            tipo_saldo=SALDO_CHEIO,
            quantidade=-quantidade,
            usuario=usuario,
            pedido_id=pedido_id,
            codigo_pedido=codigo_pedido,
        )

    def registrar_entrada_vazio(self, produto, quantidade, usuario, pedido_id, codigo_pedido, motivo):
        return self._aplicar(
            produto_id=produto.id,
            tipo=TIPO_ENTRADA_VAZIO,
            tipo_saldo=SALDO_SECO,
            quantidade=quantidade,
            usuario=usuario,
            motivo=motivo,
            pedido_id=pedido_id,
            codigo_pedido=codigo_pedido,
        )

    def registrar_estorno_cheio(self, produto, quantidade, usuario, pedido_id, codigo_pedido, motivo):
        return self._aplicar(
            produto_id=produto.id,
            tipo=TIPO_ESTORNO_CANCELAMENTO,
            tipo_saldo=SALDO_CHEIO,
            quantidade=quantidade,
            usuario=usuario,
            motivo=motivo,
            pedido_id=pedido_id,
            codigo_pedido=codigo_pedido,
        )

    def registrar_saida_vazio(self, produto, quantidade, usuario, pedido_id, codigo_pedido, motivo):
        return self._aplicar(
            produto_id=produto.id,
            tipo=TIPO_SAIDA_VAZIO,
            tipo_saldo=SALDO_SECO,
            quantidade=-quantidade,
            usuario=usuario,
            motivo=motivo,
            pedido_id=pedido_id,
            codigo_pedido=codigo_pedido,
        )

    def _aplicar(
        self,
        produto_id,
        tipo,
        tipo_saldo,
        quantidade,
        usuario,
        motivo='',
        custo_unitario=None,
        fornecedor=None,
        cliente=None,
        pedido_id=None,
        codigo_pedido='',
        produto_bloqueado=None,
    ):
        from .models import MovimentacaoEstoque

        if produto_bloqueado is not None:
            produto = produto_bloqueado
        else:
            produto = MovimentacaoHelpers().bloquear_produto(produto_id)
        campo = 'saldo_cheio' if tipo_saldo == SALDO_CHEIO else 'saldo_seco'
        saldo_anterior = getattr(produto, campo)
        saldo_novo, quantidade_aplicada = MovimentacaoRules().validar_delta(
            saldo_anterior,
            quantidade,
            tipo_saldo,
            produto.nome,
        )
        setattr(produto, campo, saldo_novo)
        produto.save(update_fields=[campo, 'updated_at'])
        return MovimentacaoEstoque.objects.create(
            produto=produto,
            nome_produto=produto.nome,
            tipo=tipo,
            tipo_saldo=tipo_saldo,
            quantidade=quantidade_aplicada,
            saldo_anterior=saldo_anterior,
            saldo_novo=saldo_novo,
            custo_unitario=custo_unitario,
            fornecedor=fornecedor,
            nome_fornecedor='' if fornecedor is None else fornecedor.nome_fantasia,
            cliente=cliente,
            nome_cliente='' if cliente is None else cliente.nome,
            pedido_id=pedido_id,
            codigo_pedido=codigo_pedido,
            motivo=motivo,
            usuario=usuario,
            nome_usuario=usuario.colaborador.nome,
        )

    def _auditar(self, usuario, acao, entidade_id, descricao):
        from Auditoria.auditoria.business import RegistroAuditoriaBusiness

        RegistroAuditoriaBusiness().registrar(
            acao=acao,
            tipo_entidade='ESTOQUE',
            entidade_id=entidade_id,
            descricao=descricao,
            usuario=usuario,
        )
