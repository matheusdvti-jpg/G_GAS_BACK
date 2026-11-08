from AppCore.core.permissions.permissions import (
    AllowAnyPermission,
    PedidoLeituraPermission,
    PermissaoPerfilPermission,
    UsuarioAtivoPermission,
)


class AllowAnyMixin:
    permission_classes = [AllowAnyPermission]
    authentication_classes = []


class AutenticadoMixin:
    permission_classes = [UsuarioAtivoPermission]


class PermissaoMixin:
    permission_classes = [UsuarioAtivoPermission, PermissaoPerfilPermission]
    permissao = None


class PedidoLeituraMixin:
    permission_classes = [UsuarioAtivoPermission, PedidoLeituraPermission]
