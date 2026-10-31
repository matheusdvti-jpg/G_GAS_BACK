from django.core.management.base import BaseCommand

from Colaboradores.colaboradores.business import ColaboradorBusiness
from Colaboradores.colaboradores.choices import PERFIL_ADMINISTRADOR
from Colaboradores.colaboradores.models import User

USERNAME_ADMIN = 'admin'
EMAIL_ADMIN = 'admin@ggas.com.br'
SENHA_ADMIN = 'Ggas@123'
CPF_ADMIN = '52998224725'


class Command(BaseCommand):
    help = 'Cria o administrador inicial para o SQLite local.'

    def handle(self, *args, **options):
        if User.objects.filter(username=USERNAME_ADMIN).exists():
            self.stdout.write(
                f'Administrador inicial já existe. Usuário: {USERNAME_ADMIN} E-mail: {EMAIL_ADMIN}'
            )
            return

        colaborador = ColaboradorBusiness().criar(
            {
                'nome': 'Administrador',
                'cpf': CPF_ADMIN,
                'telefone': '11987654321',
                'perfil': PERFIL_ADMINISTRADOR,
                'ativo': True,
                'conta': {
                    'username': USERNAME_ADMIN,
                    'email': EMAIL_ADMIN,
                    'password': SENHA_ADMIN,
                },
            }
        )
        conta = colaborador.conta
        conta.is_staff = True
        conta.is_superuser = True
        conta.save(update_fields=['is_staff', 'is_superuser', 'updated_at'])
        self.stdout.write(
            f'Administrador criado. Usuário: {USERNAME_ADMIN} E-mail: {EMAIL_ADMIN} Senha: {SENHA_ADMIN}'
        )
