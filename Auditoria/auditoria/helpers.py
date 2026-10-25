from AppCore.core.helpers.helpers import ModelInstanceHelpers


class RegistroAuditoriaHelpers(ModelInstanceHelpers):
    def para_consulta(self):
        from .models import RegistroAuditoria

        return RegistroAuditoria.objects.select_related('usuario', 'usuario__colaborador')
