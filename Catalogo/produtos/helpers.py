from AppCore.core.exceptions.exceptions import NotFoundException
from AppCore.core.helpers.helpers import ModelInstanceHelpers


class ProdutoHelpers(ModelInstanceHelpers):
    def bloquear(self, produto_id):
        from .models import Produto

        try:
            return Produto.objects.select_for_update().get(pk=produto_id)
        except Produto.DoesNotExist:
            raise NotFoundException('Produto não encontrado.')
