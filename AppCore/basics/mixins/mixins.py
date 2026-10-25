from AppCore.core.permissions.permissions import (
    AllowAnyPermission,
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
