from rest_framework.pagination import LimitOffsetPagination


class PaginacaoPadrao(LimitOffsetPagination):
    """Página padrão de 20. Um pedido não passa de 100 linhas."""

    default_limit = 20
    max_limit = 100
