from Colaboradores.colaboradores.choices import (
    PERFIL_ADMINISTRADOR,
    PERFIL_ATENDENTE,
    PERFIL_ENTREGADOR,
    PERFIL_ESTOQUISTA,
    PERFIL_GERENTE,
)

PERMISSOES = {
    'nova_venda': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE, PERFIL_ATENDENTE},
    'conceder_desconto': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE, PERFIL_ATENDENTE},
    'cancelar_venda': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE},
    'entrada_estoque': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE, PERFIL_ESTOQUISTA},
    'saida_manual_estoque': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE, PERFIL_ESTOQUISTA},
    'conferencia_inventario': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE, PERFIL_ESTOQUISTA},
    # Rótulo do painel. Nenhuma rota usa este código.
    'gestao_cadastros': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE, PERFIL_ATENDENTE},
    'cadastrar_cliente': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE, PERFIL_ATENDENTE},
    'gerir_produto': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE},
    'gerir_fornecedor': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE},
    'gestao_colaboradores': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE},
    'relatorios_financeiros': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE},
    'auditoria_sistema': {PERFIL_ADMINISTRADOR},
    'confirmar_entrega': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE, PERFIL_ENTREGADOR},
    'reabrir_pedido': {PERFIL_ADMINISTRADOR, PERFIL_GERENTE},
}


def usuario_pode(usuario, codigo):
    if getattr(usuario, 'is_superuser', False):
        return True
    colaborador = getattr(usuario, 'colaborador', None)
    if colaborador is None:
        return False
    if colaborador.perfil == PERFIL_ADMINISTRADOR:
        return True
    return colaborador.perfil in PERMISSOES.get(codigo, set())
