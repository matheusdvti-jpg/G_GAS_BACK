from AppCore.core.rules.rules import ModelInstanceRules


class ClienteRules(ModelInstanceRules):
    def validar_novo(self, dados):
        self._validar_campos(dados, criacao=True)
        return True

    def validar_atualizacao(self, dados):
        self._validar_campos(dados, criacao=False)
        return True

    def _validar_campos(self, dados, criacao):
        if criacao or 'nome' in dados:
            nome = (dados.get('nome') or '').strip()
            if len(nome) < 3:
                self.return_exception('Informe o nome do cliente.')
            dados['nome'] = nome

        if criacao or 'telefone' in dados:
            dados['telefone'] = self._normalizar_telefone(dados.get('telefone'), obrigatorio=True)

        if 'telefone_secundario' in dados or criacao:
            dados['telefone_secundario'] = self._normalizar_telefone(
                dados.get('telefone_secundario'),
                obrigatorio=False,
            )

        if criacao or 'logradouro' in dados:
            logradouro = (dados.get('logradouro') or '').strip()
            if len(logradouro) < 3:
                self.return_exception('Informe o logradouro do cliente.')
            dados['logradouro'] = logradouro

        if criacao or 'numero' in dados:
            numero = (dados.get('numero') or '').strip()
            if not numero:
                self.return_exception('Informe o número do endereço.')
            dados['numero'] = numero

        if 'complemento' in dados or criacao:
            dados['complemento'] = (dados.get('complemento') or '').strip()

        if criacao or 'bairro' in dados:
            bairro = (dados.get('bairro') or '').strip()
            if len(bairro) < 2:
                self.return_exception('Informe o bairro do cliente.')
            dados['bairro'] = bairro

        if criacao or 'cidade' in dados:
            cidade = (dados.get('cidade') or '').strip()
            if len(cidade) < 2:
                self.return_exception('Informe a cidade do cliente.')
            dados['cidade'] = cidade

        if criacao or 'ponto_referencia' in dados:
            referencia = (dados.get('ponto_referencia') or '').strip()
            if len(referencia) < 3:
                self.return_exception('Informe o ponto de referência para a entrega.')
            dados['ponto_referencia'] = referencia

        if 'observacoes' in dados or criacao:
            dados['observacoes'] = (dados.get('observacoes') or '').strip()

    def _normalizar_telefone(self, valor, obrigatorio):
        digitos = ''.join(caractere for caractere in str(valor or '') if caractere.isdigit())
        if not digitos and not obrigatorio:
            return ''
        if len(digitos) not in (10, 11):
            self.return_exception('Informe um telefone com DDD e 10 ou 11 dígitos.')
        return digitos
