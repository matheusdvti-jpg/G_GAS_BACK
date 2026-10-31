from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from AppCore.core.rules.rules import ModelInstanceRules

from .choices import PERFIL_ADMINISTRADOR, PERFIL_CHOICES, PERFIL_ENTREGADOR


class ColaboradorRules(ModelInstanceRules):
    def validar_novo(self, dados):
        self._validar_campos(dados, criacao=True)
        from .models import Colaborador

        if dados.get('cpf') and Colaborador.objects.filter(cpf=dados['cpf']).exists():
            self.return_exception('Já existe um colaborador com este CPF.')
        return True

    def validar_atualizacao(self, dados):
        self._validar_campos(dados, criacao=False)
        if 'cpf' in dados and dados['cpf'] != self.object_instance.cpf:
            from .models import Colaborador

            antigo = self.object_instance.cpf
            novo = dados['cpf']
            perfil = dados.get('perfil', self.object_instance.perfil)
            pode_ajustar = (not antigo and novo) or (perfil == PERFIL_ENTREGADOR and not novo)
            if not pode_ajustar:
                self.return_exception('O CPF do colaborador não pode ser alterado.')
            if novo and Colaborador.objects.filter(cpf=novo).exclude(pk=self.object_instance.pk).exists():
                self.return_exception('Já existe um colaborador com este CPF.')
        self._validar_ultimo_administrador(dados)
        return True

    def validar_sem_conta(self, conta):
        if conta is not None:
            self.return_exception('Este colaborador já possui conta de acesso.')
        return True

    def validar_com_conta(self, conta):
        if conta is None:
            self.return_exception('Este colaborador ainda não possui conta de acesso.')
        return True

    def validar_conta(self, dados, conta_existente=None):
        username = (dados.get('username') or '').strip().lower()
        email = (dados.get('email') or '').strip().lower()
        senha = dados.get('password') or ''

        if len(username) < 3:
            self.return_exception('O usuário de acesso precisa ter ao menos 3 caracteres.')
        if not email or '@' not in email:
            self.return_exception('Informe um e-mail válido para a conta.')

        from .models import User

        username_qs = User.objects.filter(username=username)
        email_qs = User.objects.filter(email=email)
        if conta_existente is not None:
            username_qs = username_qs.exclude(pk=conta_existente.pk)
            email_qs = email_qs.exclude(pk=conta_existente.pk)
        if username_qs.exists():
            self.return_exception('Já existe uma conta com este usuário.')
        if email_qs.exists():
            self.return_exception('Já existe uma conta com este e-mail.')

        if conta_existente is None or senha:
            try:
                validate_password(senha, user=conta_existente)
            except DjangoValidationError as exc:
                self.return_exception(' '.join(exc.messages))

        dados['username'] = username
        dados['email'] = email
        return True

    def _validar_campos(self, dados, criacao):
        if criacao or 'nome' in dados:
            nome = (dados.get('nome') or '').strip()
            if len(nome) < 3:
                self.return_exception('Informe o nome completo do colaborador.')
            dados['nome'] = nome

        if criacao or 'telefone' in dados:
            telefone = (dados.get('telefone') or '').strip()
            if len(telefone) < 8:
                self.return_exception('Informe um telefone válido.')
            dados['telefone'] = telefone

        if criacao or 'perfil' in dados:
            perfil = dados.get('perfil')
            perfis = {codigo for codigo, _rotulo in PERFIL_CHOICES}
            if perfil not in perfis:
                self.return_exception('Perfil de colaborador inválido.')

        if criacao or 'cpf' in dados:
            perfil = dados.get('perfil')
            if not perfil and not criacao:
                perfil = self.object_instance.perfil
            bruto = str(dados.get('cpf') or '').strip()
            if not bruto:
                if perfil == PERFIL_ENTREGADOR:
                    dados['cpf'] = None
                else:
                    self.return_exception('Informe o CPF com 11 dígitos.')
            else:
                dados['cpf'] = self._normalizar_cpf(bruto)

        if 'placa_veiculo' in dados or criacao:
            dados['placa_veiculo'] = (dados.get('placa_veiculo') or '').strip().upper()

    def _validar_ultimo_administrador(self, dados):
        from .models import Colaborador

        colaborador = self.object_instance
        era_admin_ativo = colaborador.perfil == PERFIL_ADMINISTRADOR and colaborador.ativo
        perfil_final = dados.get('perfil', colaborador.perfil)
        ativo_final = dados.get('ativo', colaborador.ativo)
        continua_admin_ativo = perfil_final == PERFIL_ADMINISTRADOR and ativo_final
        if not era_admin_ativo or continua_admin_ativo:
            return
        existe_outro = Colaborador.objects.filter(
            perfil=PERFIL_ADMINISTRADOR,
            ativo=True,
        ).exclude(pk=colaborador.pk).exists()
        if not existe_outro:
            self.return_exception('É necessário manter ao menos um administrador ativo.')

    def _normalizar_cpf(self, valor):
        digitos = ''.join(caractere for caractere in str(valor) if caractere.isdigit())
        if len(digitos) != 11:
            self.return_exception('Informe o CPF com 11 dígitos.')
        return digitos


class UserRules(ModelInstanceRules):
    def pode_autenticar(self):
        usuario = self.object_instance
        if not usuario.is_active:
            self.return_exception('Usuário inativo.')
        if not usuario.colaborador.ativo:
            self.return_exception('Colaborador inativo.')
        return True
