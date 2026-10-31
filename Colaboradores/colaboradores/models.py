from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from AppCore.basics.models.models import Base404ExceptionUserManager, BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .business import ColaboradorBusiness, UserBusiness
from .choices import PERFIL_CHOICES
from .helpers import ColaboradorHelpers, UserHelpers
from .rules import ColaboradorRules, UserRules


class UserManager(Base404ExceptionUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('O usuário deve ter um nome de acesso')
        if not email:
            raise ValueError('O usuário deve ter um e-mail')
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        usuario = self.model(
            username=self.model.normalize_username(username),
            email=self.normalize_email(email),
            **extra_fields,
        )
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, username, email, password=None, **extra_fields):
        from .choices import PERFIL_ADMINISTRADOR

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        nome = extra_fields.pop('nome', username)
        cpf = extra_fields.pop('cpf', None)
        if cpf is None:
            cpf = f'{(self.model.objects.count() + 1):011d}'
        colaborador = extra_fields.pop('colaborador', None)
        if colaborador is None:
            colaborador = Colaborador.objects.create(
                nome=nome,
                cpf=''.join(caractere for caractere in str(cpf) if caractere.isdigit()),
                telefone=extra_fields.pop('telefone', '0000000000'),
                perfil=PERFIL_ADMINISTRADOR,
                ativo=True,
            )
        return self.create_user(
            username=username,
            email=email,
            password=password,
            colaborador=colaborador,
            **extra_fields,
        )


class Colaborador(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    helper_class = ColaboradorHelpers
    business_class = ColaboradorBusiness
    rules_class = ColaboradorRules

    nome = models.CharField('Nome', max_length=150)
    cpf = models.CharField('CPF', max_length=11, unique=True, null=True, blank=True)
    telefone = models.CharField('Telefone', max_length=20)
    perfil = models.CharField('Perfil', max_length=20, choices=PERFIL_CHOICES)
    ativo = models.BooleanField('Ativo', default=True)
    placa_veiculo = models.CharField('Placa do veículo', max_length=40, blank=True, default='')

    class Meta:
        verbose_name = 'Colaborador'
        verbose_name_plural = 'Colaboradores'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.get_perfil_display()})'


class User(
    ModelHelperMixin,
    ModelBusinessMixin,
    ModelRulesMixin,
    AbstractBaseUser,
    PermissionsMixin,
    BasicModel,
):
    helper_class = UserHelpers
    business_class = UserBusiness
    rules_class = UserRules

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    username = models.CharField('Usuário', max_length=150, unique=True)
    email = models.EmailField('E-mail', unique=True)
    colaborador = models.OneToOneField(
        Colaborador,
        verbose_name='Colaborador',
        on_delete=models.PROTECT,
        related_name='conta',
    )
    avatar_url = models.URLField('Avatar', blank=True, default='')
    is_active = models.BooleanField('Ativo', default=True)
    is_staff = models.BooleanField('Acesso ao admin', default=False)

    objects = UserManager()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return self.username
