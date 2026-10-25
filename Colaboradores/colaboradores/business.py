from AppCore.core.business.business import ModelInstanceBusiness


class ColaboradorBusiness(ModelInstanceBusiness):
    def criar(self, dados, usuario=None):
        from .models import Colaborador
        from .rules import ColaboradorRules

        conta = dados.pop('conta', None)
        ColaboradorRules().validar_novo(dados)
        colaborador = Colaborador.objects.create(
            nome=dados['nome'],
            cpf=dados['cpf'],
            telefone=dados['telefone'],
            perfil=dados['perfil'],
            ativo=dados.get('ativo', True),
            placa_veiculo=dados.get('placa_veiculo', ''),
        )
        if conta:
            colaborador.business.criar_conta(conta, usuario=usuario)
        self._auditar(
            usuario,
            'CRIAR_COLABORADOR',
            colaborador.id,
            f'Colaborador {colaborador.nome} cadastrado com perfil {colaborador.perfil}.',
        )
        return colaborador

    def atualizar(self, dados, usuario=None):
        from .helpers import ColaboradorHelpers

        self.object_instance = ColaboradorHelpers().bloquear(self.object_instance.pk)
        antes = {
            campo: getattr(self.object_instance, campo)
            for campo in ('nome', 'telefone', 'perfil', 'ativo', 'placa_veiculo')
        }
        self.object_instance.rules.validar_atualizacao(dados)
        alterados = [campo for campo in antes if campo in dados]
        for campo in alterados:
            setattr(self.object_instance, campo, dados[campo])
        if alterados:
            self.object_instance.save(update_fields=[*alterados, 'updated_at'])
        self._sincronizar_conta()
        self._auditar(
            usuario,
            'ATUALIZAR_COLABORADOR',
            self.object_instance.id,
            f'Colaborador {self.object_instance.nome} atualizado.',
            self._alteracoes(antes, self.object_instance, tuple(antes)),
        )
        return self.object_instance

    def criar_conta(self, dados, usuario=None):
        from .models import User

        conta = self.object_instance.helper.conta_ou_nenhuma()
        self.object_instance.rules.validar_sem_conta(conta)
        self.object_instance.rules.validar_conta(dados)
        conta = User.objects.create_user(
            username=dados['username'],
            email=dados['email'],
            password=dados['password'],
            colaborador=self.object_instance,
            is_active=self.object_instance.ativo,
        )
        self._auditar(
            usuario,
            'CRIAR_CONTA',
            self.object_instance.id,
            f'Conta {conta.username} vinculada a {self.object_instance.nome}.',
            tipo_entidade='CONTA',
        )
        return conta

    def atualizar_conta(self, dados, usuario=None):
        conta = self.object_instance.helper.conta_ou_nenhuma()
        self.object_instance.rules.validar_com_conta(conta)
        username_anterior = conta.username
        email_anterior = conta.email
        dados_completos = {
            'username': dados.get('username', conta.username),
            'email': dados.get('email', conta.email),
            'password': dados.get('password') or '',
        }
        self.object_instance.rules.validar_conta(dados_completos, conta_existente=conta)
        conta.username = dados_completos['username']
        conta.email = dados_completos['email']
        senha_alterada = bool(dados_completos['password'])
        if senha_alterada:
            conta.set_password(dados_completos['password'])
        conta.save()
        alteracoes = {}
        if conta.username != username_anterior:
            alteracoes['username'] = {'antes': username_anterior, 'depois': conta.username}
        if conta.email != email_anterior:
            alteracoes['email'] = {'antes': email_anterior, 'depois': conta.email}
        if senha_alterada:
            alteracoes['senha_alterada'] = True
        self._auditar(
            usuario,
            'ATUALIZAR_CONTA',
            self.object_instance.id,
            f'Conta de {self.object_instance.nome} atualizada.',
            alteracoes,
            tipo_entidade='CONTA',
        )
        return conta

    def _sincronizar_conta(self):
        conta = self.object_instance.helper.conta_ou_nenhuma()
        if conta is None or conta.is_active == self.object_instance.ativo:
            return
        conta.is_active = self.object_instance.ativo
        conta.save(update_fields=['is_active', 'updated_at'])

    def _auditar(self, usuario, acao, entidade_id, descricao, alteracoes=None, tipo_entidade='COLABORADOR'):
        if usuario is None:
            return
        from Auditoria.auditoria.business import RegistroAuditoriaBusiness

        RegistroAuditoriaBusiness().registrar(
            acao=acao,
            tipo_entidade=tipo_entidade,
            entidade_id=entidade_id,
            descricao=descricao,
            usuario=usuario,
            alteracoes=alteracoes,
        )

    def _alteracoes(self, antes, objeto, campos):
        mudancas = {}
        for campo in campos:
            depois = getattr(objeto, campo)
            if antes[campo] != depois:
                mudancas[campo] = {'antes': antes[campo], 'depois': depois}
        return mudancas


class UserBusiness(ModelInstanceBusiness):
    pass
