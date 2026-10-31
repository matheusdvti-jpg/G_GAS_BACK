from decimal import Decimal

from AppCore.core.rules.rules import ModelInstanceRules

from .choices import CATEGORIA_CHOICES


class ProdutoRules(ModelInstanceRules):
    def validar_novo(self, dados):
        self._validar_campos(dados, criacao=True)
        self._validar_codigo_unico(dados['codigo'])
        return True

    def validar_atualizacao(self, dados):
        self._validar_campos(dados, criacao=False)
        if 'codigo' in dados:
            self._validar_codigo_unico(dados['codigo'], ignorar_id=self.object_instance.id)
        for campo in ('saldo_cheio', 'saldo_seco'):
            if campo in dados and dados[campo] != getattr(self.object_instance, campo):
                self.return_exception('O saldo do produto só muda por movimentação de estoque.')
        return True

    def _validar_campos(self, dados, criacao):
        if criacao or 'codigo' in dados:
            codigo = (dados.get('codigo') or '').strip().upper()
            if not codigo:
                if not criacao:
                    self.return_exception('Informe o código do produto.')
                codigo = self._codigo_gerado()
            elif len(codigo) < 2:
                self.return_exception('Informe o código do produto.')
            dados['codigo'] = codigo

        if criacao or 'nome' in dados:
            nome = (dados.get('nome') or '').strip()
            if len(nome) < 3:
                self.return_exception('Informe o nome do produto.')
            dados['nome'] = nome

        if criacao or 'descricao' in dados:
            descricao = (dados.get('descricao') or '').strip()
            if not descricao:
                self.return_exception('Informe a descrição do produto.')
            dados['descricao'] = descricao

        if criacao or 'marca' in dados:
            dados['marca'] = (dados.get('marca') or '').strip()

        if criacao or 'categoria' in dados:
            categorias = {codigo for codigo, _rotulo in CATEGORIA_CHOICES}
            categoria = dados.get('categoria') or ''
            if categoria and categoria not in categorias:
                self.return_exception('Categoria inválida. Use GAS, AGUA ou ACESSORIO.')
            dados['categoria'] = categoria

        if criacao or 'preco_venda' in dados:
            dados['preco_venda'] = self._decimal_nao_negativo(dados.get('preco_venda'), 'preço')

        if criacao or 'preco_custo' in dados:
            dados['preco_custo'] = self._decimal_nao_negativo(dados.get('preco_custo'), 'valor')

        for campo, rotulo in (
            ('saldo_cheio', 'saldo cheio'),
            ('saldo_seco', 'saldo seco'),
            ('estoque_minimo', 'estoque mínimo'),
        ):
            if criacao or campo in dados:
                dados[campo] = self._inteiro_nao_negativo(dados.get(campo, 0), rotulo)

        if criacao or 'unidade' in dados:
            dados['unidade'] = (dados.get('unidade') or '').strip()

        if 'ativo' not in dados and criacao:
            dados['ativo'] = True

    def _validar_codigo_unico(self, codigo, ignorar_id=None):
        from .models import Produto

        consulta = Produto.objects.filter(codigo=codigo)
        if ignorar_id is not None:
            consulta = consulta.exclude(pk=ignorar_id)
        if consulta.exists():
            self.return_exception('Já existe um produto com este código.')

    def _decimal_nao_negativo(self, valor, rotulo):
        try:
            numero = Decimal(str(valor))
        except Exception:
            self.return_exception(f'Informe um {rotulo} válido.')
        if numero < 0:
            self.return_exception(f'O {rotulo} não pode ser negativo.')
        return numero.quantize(Decimal('0.01'))

    def _inteiro_nao_negativo(self, valor, rotulo):
        try:
            numero = int(valor)
        except (TypeError, ValueError):
            self.return_exception(f'Informe um {rotulo} válido.')
        if numero < 0:
            self.return_exception(f'O {rotulo} não pode ser negativo.')
        return numero

    def _codigo_gerado(self):
        from django.utils import timezone

        from .models import Produto

        base = timezone.now().strftime('P%y%m%d%H%M%S')
        codigo = base
        sufixo = 1
        while Produto.objects.filter(codigo=codigo).exists():
            codigo = f'{base}-{sufixo}'
            sufixo += 1
        return codigo
