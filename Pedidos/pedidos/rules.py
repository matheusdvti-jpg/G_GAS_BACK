from decimal import Decimal

from AppCore.core.exceptions.exceptions import AuthorizationException
from AppCore.core.rules.rules import ModelInstanceRules

from Colaboradores.colaboradores.choices import PERFIL_ENTREGADOR
from Colaboradores.colaboradores.permissoes import usuario_pode

from .choices import (
    DESCONTO_NENHUM,
    DESCONTO_PERCENTUAL,
    DESCONTO_VALOR,
    PAGAMENTO_DINHEIRO,
    STATUS_CANCELADO,
    STATUS_ENTREGUE,
    STATUS_PENDENTE,
)


class PedidoRules(ModelInstanceRules):
    def validar_composicao(self, itens):
        if not itens:
            self.return_exception('Adicione ao menos um produto ao pedido.')
        identificadores = [item['produto_id'] for item in itens]
        if len(set(identificadores)) != len(identificadores):
            self.return_exception('Produto repetido no pedido. Ajuste a quantidade.')
        return True

    def validar_desconto(self, tipo, valor, usuario):
        if tipo == DESCONTO_NENHUM:
            return Decimal('0.00')
        if tipo not in (DESCONTO_VALOR, DESCONTO_PERCENTUAL):
            self.return_exception('Tipo de desconto inválido.')
        try:
            numero = Decimal(str(valor or 0))
        except Exception:
            self.return_exception('Informe um desconto válido.')
        if numero < 0:
            self.return_exception('O desconto não pode ser negativo.')
        if tipo == DESCONTO_PERCENTUAL and numero > 100:
            self.return_exception('O desconto percentual não pode passar de 100.')
        if numero > 0 and not usuario_pode(usuario, 'conceder_desconto'):
            raise AuthorizationException('Você não pode conceder desconto.')
        return numero.quantize(Decimal('0.01'))

    def validar_pagamento(self, forma, total, valor_recebido):
        if forma == PAGAMENTO_DINHEIRO:
            recebido = total if valor_recebido is None else Decimal(str(valor_recebido)).quantize(Decimal('0.01'))
            if recebido < total:
                self.return_exception(
                    f'Valor recebido em dinheiro (R$ {recebido:.2f}) é menor que o total (R$ {total:.2f}).'
                )
            return recebido, (recebido - total).quantize(Decimal('0.01'))
        return None, Decimal('0.00')

    def validar_entregador(self, entregador):
        if entregador is None or entregador.perfil != PERFIL_ENTREGADOR or not entregador.ativo:
            self.return_exception('Entregador responsável inválido.')
        return True

    def validar_item(self, produto, quantidade, vazios_informados):
        if not produto.ativo:
            self.return_exception(f'Produto inativo: {produto.nome}.')
        if quantidade <= 0:
            self.return_exception('A quantidade do item deve ser maior que zero.')
        if produto.saldo_cheio < quantidade:
            self.return_exception(
                f'Estoque insuficiente para {produto.nome}. '
                f'Disponível: {produto.saldo_cheio}, Solicitado: {quantidade}'
            )
        vazios, nome_vazio = self._vazios(produto, quantidade, vazios_informados)
        return vazios, nome_vazio

    def pode_transitar(self, novo_status, usuario, observacao):
        atual = self.object_instance.status
        if atual == novo_status:
            return True
        if atual == STATUS_CANCELADO:
            self.return_exception('Pedido cancelado não muda de status.')
        if novo_status == STATUS_CANCELADO:
            if not usuario_pode(usuario, 'cancelar_venda'):
                raise AuthorizationException('Você não pode cancelar venda.')
            if len((observacao or '').strip()) < 3:
                self.return_exception('Informe o motivo do cancelamento.')
            return True
        if atual == STATUS_PENDENTE and novo_status == STATUS_ENTREGUE:
            if not usuario_pode(usuario, 'confirmar_entrega'):
                raise AuthorizationException('Você não pode confirmar a entrega.')
            entregador = usuario.colaborador
            if entregador.perfil == PERFIL_ENTREGADOR and entregador.id != self.object_instance.entregador_id:
                raise AuthorizationException('O entregador só confirma a própria entrega.')
            return True
        if atual == STATUS_ENTREGUE and novo_status == STATUS_PENDENTE:
            if not usuario_pode(usuario, 'reabrir_pedido'):
                raise AuthorizationException('Você não pode reabrir o pedido.')
            return True
        self.return_exception('Transição de status inválida.')

    def _vazios(self, produto, quantidade, vazios_informados):
        if produto.categoria == 'GAS':
            return quantidade, 'botijão seco'
        if produto.categoria == 'AGUA':
            recebidos = 0 if vazios_informados is None else int(vazios_informados)
            if recebidos != quantidade:
                frase = '1 galão vazio' if quantidade == 1 else f'{quantidade} galões vazios'
                self.return_exception(
                    f'Para vender {quantidade} un. de {produto.nome}, '
                    f'o cliente precisa entregar {frase}. Recebido: {recebidos}.'
                )
            return recebidos, 'galão vazio'
        return 0, ''
