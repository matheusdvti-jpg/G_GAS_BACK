from AppCore.core.rules.rules import ModelInstanceRules


class FornecedorRules(ModelInstanceRules):
    def validar_novo(self, dados):
        self._validar_campos(dados, criacao=True)
        self._validar_cnpj_unico(dados['cnpj'])
        return True

    def validar_atualizacao(self, dados):
        self._validar_campos(dados, criacao=False)
        if 'cnpj' in dados:
            self._validar_cnpj_unico(dados['cnpj'], ignorar_id=self.object_instance.id)
        return True

    def _validar_campos(self, dados, criacao):
        if criacao or 'nome_fantasia' in dados:
            nome = (dados.get('nome_fantasia') or '').strip()
            if len(nome) < 2:
                self.return_exception('Informe o nome fantasia do fornecedor.')
            dados['nome_fantasia'] = nome

        if criacao or 'razao_social' in dados:
            razao = (dados.get('razao_social') or '').strip()
            if len(razao) < 3:
                self.return_exception('Informe a razão social do fornecedor.')
            dados['razao_social'] = razao

        if criacao or 'cnpj' in dados:
            dados['cnpj'] = self._normalizar_cnpj(dados.get('cnpj'))

        if criacao or 'telefone' in dados:
            dados['telefone'] = self._normalizar_telefone(dados.get('telefone'))

        if criacao or 'nome_contato' in dados:
            contato = (dados.get('nome_contato') or '').strip()
            if len(contato) < 3:
                self.return_exception('Informe o nome do contato no fornecedor.')
            dados['nome_contato'] = contato

        if criacao or 'endereco' in dados:
            endereco = (dados.get('endereco') or '').strip()
            if len(endereco) < 3:
                self.return_exception('Informe o endereço do fornecedor.')
            dados['endereco'] = endereco

        if criacao or 'cidade' in dados:
            cidade = (dados.get('cidade') or '').strip()
            if len(cidade) < 2:
                self.return_exception('Informe a cidade do fornecedor.')
            dados['cidade'] = cidade

        if 'produtos_fornecidos' in dados or criacao:
            nomes = dados.get('produtos_fornecidos') or []
            if not isinstance(nomes, list):
                self.return_exception('A lista de produtos fornecidos é inválida.')
            dados['produtos_fornecidos'] = [str(nome).strip() for nome in nomes if str(nome).strip()]

        if 'ativo' not in dados and criacao:
            dados['ativo'] = True

    def _validar_cnpj_unico(self, cnpj, ignorar_id=None):
        from .models import Fornecedor

        consulta = Fornecedor.objects.filter(cnpj=cnpj)
        if ignorar_id is not None:
            consulta = consulta.exclude(pk=ignorar_id)
        if consulta.exists():
            self.return_exception('Já existe um fornecedor com este CNPJ.')

    def _normalizar_cnpj(self, valor):
        digitos = ''.join(caractere for caractere in str(valor or '') if caractere.isdigit())
        if not self._cnpj_valido(digitos):
            self.return_exception('CNPJ inválido.')
        return digitos

    def _cnpj_valido(self, cnpj):
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False

        def digito(base, pesos):
            total = sum(int(numero) * peso for numero, peso in zip(base, pesos))
            resto = total % 11
            return '0' if resto < 2 else str(11 - resto)

        pesos_primeiro = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos_segundo = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        if digito(cnpj[:12], pesos_primeiro) != cnpj[12]:
            return False
        return digito(cnpj[:13], pesos_segundo) == cnpj[13]

    def _normalizar_telefone(self, valor):
        digitos = ''.join(caractere for caractere in str(valor or '') if caractere.isdigit())
        if len(digitos) not in (10, 11):
            self.return_exception('Informe um telefone com DDD e 10 ou 11 dígitos.')
        return digitos
