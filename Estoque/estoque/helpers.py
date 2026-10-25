from AppCore.core.exceptions.exceptions import NotFoundException
from AppCore.core.helpers.helpers import ModelInstanceHelpers


class MovimentacaoHelpers(ModelInstanceHelpers):
    def para_consulta(self):
        from .models import MovimentacaoEstoque

        return MovimentacaoEstoque.objects.select_related('produto', 'fornecedor', 'cliente', 'usuario')

    def obter(self, modelo, identificador, mensagem):
        try:
            return modelo.objects.get(pk=identificador)
        except NotFoundException:
            raise NotFoundException(mensagem)

    def bloquear_produto(self, produto_id):
        from Catalogo.produtos.models import Produto

        try:
            return Produto.objects.select_for_update().get(pk=produto_id)
        except Produto.DoesNotExist:
            raise NotFoundException('Produto não encontrado.')
