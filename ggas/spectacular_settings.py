SPECTACULAR_SETTINGS = {
    'TITLE': 'G-GÁS API',
    'DESCRIPTION': 'API do painel da distribuidora de gás e água mineral.',
    'VERSION': '0.1.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'ENUM_NAME_OVERRIDES': {
        'PerfilColaboradorEnum': 'Colaboradores.colaboradores.choices.PERFIL_CHOICES',
        'CategoriaProdutoEnum': 'Catalogo.produtos.choices.CATEGORIA_CHOICES',
        'TipoEntidadeAuditoriaEnum': 'Auditoria.auditoria.choices.TIPO_ENTIDADE_CHOICES',
        'TipoMovimentacaoEstoqueEnum': 'Estoque.estoque.choices.TIPO_MOVIMENTACAO_CHOICES',
        'TipoSaldoEstoqueEnum': 'Estoque.estoque.choices.TIPO_SALDO_CHOICES',
        'StatusPedidoEnum': 'Pedidos.pedidos.choices.STATUS_PEDIDO_CHOICES',
        'FormaPagamentoEnum': 'Pedidos.pedidos.choices.FORMA_PAGAMENTO_CHOICES',
    },
}
