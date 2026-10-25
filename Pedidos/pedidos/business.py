from decimal import Decimal, ROUND_HALF_UP

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import NotFoundException

from .choices import (
    DESCONTO_PERCENTUAL,
    DESCONTO_VALOR,
    STATUS_CANCELADO,
    STATUS_PENDENTE,
)
from .helpers import PedidoHelpers
from .rules import PedidoRules


class PedidoBusiness(ModelInstanceBusiness):
    def criar(self, dados, usuario):
        from Clientes.clientes.models import Cliente
        from Colaboradores.colaboradores.models import Colaborador

        from .models import HistoricoStatusPedido, ItemPedido, Pedido

        regras = PedidoRules()
        regras.validar_composicao(dados.get('itens'))
        consulta = PedidoHelpers()
        cliente = consulta.exigir(Cliente, dados['cliente_id'], 'Cliente não encontrado.')
        entregador = consulta.exigir(Colaborador, dados['entregador_id'], 'Entregador responsável inválido.')
        regras.validar_entregador(entregador)
        tipo_desconto = dados.get('tipo_desconto') or 'NONE'
        valor_informado = regras.validar_desconto(
            tipo_desconto,
            dados.get('valor_desconto', 0),
            usuario,
        )

        produtos_ids = sorted({item['produto_id'] for item in dados['itens']})
        bloqueados = consulta.bloquear_produtos(produtos_ids)
        if len(bloqueados) != len(produtos_ids):
            regras.return_exception('Produto não encontrado.')

        linhas = []
        subtotal = Decimal('0.00')
        for item in dados['itens']:
            produto = bloqueados[item['produto_id']]
            quantidade = int(item['quantidade'])
            vazios, nome_vazio = regras.validar_item(
                produto,
                quantidade,
                item.get('vazios_recebidos'),
            )
            total_item = (produto.preco_venda * quantidade).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            subtotal += total_item
            linhas.append((produto, quantidade, vazios, nome_vazio, total_item))
        subtotal = subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        if tipo_desconto == DESCONTO_VALOR:
            desconto = min(valor_informado, subtotal)
        elif tipo_desconto == DESCONTO_PERCENTUAL:
            desconto = (subtotal * valor_informado / Decimal('100')).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP,
            )
        else:
            desconto = Decimal('0.00')
        total = max(Decimal('0.00'), (subtotal - desconto).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        valor_recebido, troco = regras.validar_pagamento(
            dados['forma_pagamento'],
            total,
            dados.get('valor_recebido'),
        )

        cliente = consulta.bloquear_cliente(cliente.id)
        codigo = consulta.proximo_codigo()
        pedido = Pedido.objects.create(
            codigo=codigo,
            cliente=cliente,
            nome_cliente=cliente.nome,
            telefone_cliente=cliente.telefone,
            logradouro=cliente.logradouro,
            numero=cliente.numero,
            complemento=cliente.complemento,
            bairro=cliente.bairro,
            cidade=cliente.cidade,
            ponto_referencia=cliente.ponto_referencia,
            subtotal=subtotal,
            tipo_desconto=tipo_desconto,
            valor_desconto=desconto,
            total=total,
            forma_pagamento=dados['forma_pagamento'],
            valor_recebido=valor_recebido,
            troco=troco,
            entregador=entregador,
            nome_entregador=entregador.nome,
            status=STATUS_PENDENTE,
            observacoes=(dados.get('observacoes') or '').strip(),
            criado_por=usuario,
            nome_criado_por=usuario.colaborador.nome,
        )
        HistoricoStatusPedido.objects.create(
            pedido=pedido,
            status=STATUS_PENDENTE,
            usuario=usuario,
            nome_usuario=usuario.colaborador.nome,
            observacao='Pedido registrado - Aguardando entrega',
        )
        for produto, quantidade, vazios, nome_vazio, total_item in linhas:
            ItemPedido.objects.create(
                pedido=pedido,
                produto=produto,
                nome_produto=produto.nome,
                marca=produto.marca,
                preco_unitario=produto.preco_venda,
                quantidade=quantidade,
                total=total_item,
                vazios_recebidos=vazios,
                nome_vazio=nome_vazio,
            )
            self._baixar_item(produto, quantidade, vazios, nome_vazio, usuario, pedido)

        cliente.total_pedidos += 1
        cliente.total_gasto = (cliente.total_gasto + total).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        cliente.save(update_fields=['total_pedidos', 'total_gasto', 'updated_at'])
        trocas = ', '.join(
            f'{vazios} {nome_vazio}' for _produto, _qtd, vazios, nome_vazio, _total in linhas if vazios
        )
        descricao = (
            f'Pedido {pedido.codigo} gerado para {cliente.nome}. '
            f'Total: R$ {total:.2f} ({pedido.forma_pagamento})'
        )
        if trocas:
            descricao = f'{descricao}. Troca recebida: {trocas}'
        self._auditar(usuario, 'CRIAR_PEDIDO', pedido.id, descricao)
        return pedido

    def alterar_status(self, novo_status, usuario, observacao=''):
        from .models import HistoricoStatusPedido

        pedido = PedidoHelpers().bloquear_pedido(self.object_instance.pk)
        if pedido.status == novo_status:
            return pedido
        pedido.rules.pode_transitar(novo_status, usuario, observacao)
        texto = (observacao or '').strip()
        if novo_status == STATUS_CANCELADO:
            self._estornar(pedido, usuario, texto)
        status_anterior = pedido.status
        pedido.status = novo_status
        pedido.save(update_fields=['status', 'updated_at'])
        HistoricoStatusPedido.objects.create(
            pedido=pedido,
            status=novo_status,
            usuario=usuario,
            nome_usuario=usuario.colaborador.nome,
            observacao=texto,
        )
        vazios = ''
        if novo_status == STATUS_CANCELADO:
            partes = [
                f'{item.vazios_recebidos} {item.nome_vazio}'
                for item in pedido.itens.all()
                if item.vazios_recebidos
            ]
            if partes:
                vazios = f" Devolver ao cliente a troca recebida: {', '.join(partes)}"
        self._auditar(
            usuario,
            'ALTERAR_STATUS_PEDIDO',
            pedido.id,
            f'Status do pedido {pedido.codigo} alterado de {status_anterior} para {novo_status}.{vazios}',
        )
        return pedido

    def _baixar_item(self, produto, quantidade, vazios, nome_vazio, usuario, pedido):
        from Estoque.estoque.business import MovimentacaoBusiness

        movimento = MovimentacaoBusiness()
        movimento.registrar_saida_venda(produto, quantidade, usuario, pedido.id, pedido.codigo)
        if vazios > 0:
            movimento.registrar_entrada_vazio(
                produto,
                vazios,
                usuario,
                pedido.id,
                pedido.codigo,
                f'Cliente entregou {vazios} {nome_vazio}',
            )

    def _estornar(self, pedido, usuario, motivo):
        from Catalogo.produtos.models import Produto
        from Estoque.estoque.business import MovimentacaoBusiness

        movimento = MovimentacaoBusiness()
        for item in PedidoHelpers().itens_para_estorno(pedido):
            try:
                produto = PedidoHelpers().buscar(Produto, item.produto_id)
            except NotFoundException:
                continue
            movimento.registrar_estorno_cheio(
                produto,
                item.quantidade,
                usuario,
                pedido.id,
                pedido.codigo,
                f'Estorno automático por cancelamento do pedido {pedido.codigo}. Motivo: {motivo}',
            )
            if item.vazios_recebidos:
                movimento.registrar_saida_vazio(
                    produto,
                    item.vazios_recebidos,
                    usuario,
                    pedido.id,
                    pedido.codigo,
                    f'Seco devolvido ao cliente no cancelamento do pedido {pedido.codigo}',
                )

    def _auditar(self, usuario, acao, entidade_id, descricao):
        from Auditoria.auditoria.business import RegistroAuditoriaBusiness

        RegistroAuditoriaBusiness().registrar(
            acao=acao,
            tipo_entidade='PEDIDO',
            entidade_id=entidade_id,
            descricao=descricao,
            usuario=usuario,
        )
