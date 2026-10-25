from django.core.exceptions import ObjectDoesNotExist

from AppCore.core.helpers.helpers import ModelInstanceHelpers


class ColaboradorHelpers(ModelInstanceHelpers):
    def resumo(self):
        colaborador = self.object_instance
        conta = colaborador.helper.conta_ou_nenhuma()
        return {
            'id': colaborador.id,
            'nome': colaborador.nome,
            'cpf': colaborador.cpf,
            'telefone': colaborador.telefone,
            'perfil': colaborador.perfil,
            'ativo': colaborador.ativo,
            'placa_veiculo': colaborador.placa_veiculo,
            'conta': None if conta is None else conta.helper.resumo(),
            'created_at': colaborador.created_at,
            'updated_at': colaborador.updated_at,
        }

    def conta_ou_nenhuma(self):
        try:
            return self.object_instance.conta
        except ObjectDoesNotExist:
            return None

    def obter(self, colaborador_id):
        from .models import Colaborador

        return Colaborador.objects.get(pk=colaborador_id)

    def bloquear(self, colaborador_id):
        from AppCore.core.exceptions.exceptions import NotFoundException

        from .models import Colaborador

        try:
            return Colaborador.objects.select_for_update().get(pk=colaborador_id)
        except Colaborador.DoesNotExist:
            raise NotFoundException('Colaborador não encontrado.')


class UserHelpers(ModelInstanceHelpers):
    def resumo(self):
        usuario = self.object_instance
        colaborador = usuario.colaborador
        return {
            'id': usuario.id,
            'username': usuario.username,
            'email': usuario.email,
            'ativo': usuario.is_active,
            'nome': colaborador.nome,
            'perfil': colaborador.perfil,
            'colaborador_id': colaborador.id,
            'avatar_url': usuario.avatar_url,
            'last_login': None if usuario.last_login is None else usuario.last_login.isoformat(),
        }

    def buscar_por_identificador(self, identificador):
        from .models import User

        texto = (identificador or '').strip()
        if '@' in texto:
            return User.objects.filter(email__iexact=texto).first()
        return User.objects.filter(username__iexact=texto).first()
