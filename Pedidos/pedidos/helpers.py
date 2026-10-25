from AppCore.core.exceptions.exceptions import BusinessRuleException, NotFoundException
from AppCore.core.helpers.helpers import ModelInstanceHelpers


class PedidoHelpers(ModelInstanceHelpers):
    def para_consulta(self):
        from .models import Pedido

        return Pedido.objects.select_related('cliente', 'entregador', 'criado_por').prefetch_related(
            'itens',
            'historico',
        )

    def exigir(self, modelo, identificador, mensagem):
        try:
            return modelo.objects.get(pk=identificador)
        except NotFoundException:
            raise BusinessRuleException(mensagem)

    def buscar(self, modelo, identificador):
        return modelo.objects.get(pk=identificador)

    def bloquear_produtos(self, identificadores):
        from Catalogo.produtos.models import Produto

        return {
            produto.id: produto
            for produto in Produto.objects.select_for_update().filter(id__in=identificadores)
        }

    def bloquear_cliente(self, cliente_id):
        from Clientes.clientes.models import Cliente

        try:
            return Cliente.objects.select_for_update().get(pk=cliente_id)
        except Cliente.DoesNotExist:
            raise NotFoundException('Cliente não encontrado.')

    def itens_para_estorno(self, pedido):
        return pedido.itens.select_related('produto')

    def bloquear_pedido(self, pedido_id):
        from .models import Pedido

        try:
            return Pedido.objects.select_for_update().get(pk=pedido_id)
        except Pedido.DoesNotExist:
            raise NotFoundException('Pedido não encontrado.')

    def proximo_codigo(self):
        from .models import SequenciaPedido

        sequencia = SequenciaPedido.objects.select_for_update().filter(nome='pedido').first()
        if sequencia is None:
            sequencia = SequenciaPedido.objects.create(nome='pedido', ultimo_numero=0)
        sequencia.ultimo_numero += 1
        sequencia.save(update_fields=['ultimo_numero'])
        return f'PED-{sequencia.ultimo_numero:06d}'
