from rest_framework.permissions import AllowAny, BasePermission

from Colaboradores.colaboradores.permissoes import usuario_pode


class AllowAnyPermission(AllowAny):
    pass


class UsuarioAtivoPermission(BasePermission):
    message = 'Usuário ou colaborador inativo.'

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario or not usuario.is_authenticated:
            return False
        if not usuario.is_active:
            return False
        colaborador = getattr(usuario, 'colaborador', None)
        if colaborador is None or not colaborador.ativo:
            return False
        return True


class PermissaoPerfilPermission(BasePermission):
    message = 'Você não tem permissão para esta ação.'

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario or not usuario.is_authenticated:
            return False
        codigo = getattr(view, 'permissao', None)
        if not codigo:
            return True
        return usuario_pode(usuario, codigo)
