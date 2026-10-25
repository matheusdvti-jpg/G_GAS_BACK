from decimal import Decimal

from AppCore.core.exceptions.exceptions import BusinessRuleException
from AppCore.core.rules.rules import ModelInstanceRules

from .choices import SALDO_CHEIO, SALDO_SECO, TIPO_SAIDA_EMPRESTIMO, TIPOS_SAIDA_MANUAL


class MovimentacaoRules(ModelInstanceRules):
    def validar_fornecedor_da_carga(self, fornecedor):
        if not fornecedor.ativo:
            self.return_exception('Fornecedor inativo não recebe carga.')
        return True

    def validar_entrada(self, quantidade, custo_unitario):
        if quantidade <= 0:
            self.return_exception('A quantidade recebida deve ser maior que zero.')
        try:
            custo = Decimal(str(custo_unitario))
        except Exception:
            self.return_exception('Informe um custo unitário válido.')
        if custo < 0:
            self.return_exception('O custo unitário não pode ser negativo.')
        return custo.quantize(Decimal('0.01'))

    def validar_saida_manual(self, tipo, quantidade, motivo, cliente):
        if tipo not in TIPOS_SAIDA_MANUAL:
            self.return_exception('Tipo de saída manual inválido.')
        if tipo == TIPO_SAIDA_EMPRESTIMO and cliente is None:
            self.return_exception('Informe o cliente do empréstimo.')
        texto = (motivo or '').strip()
        if tipo == TIPO_SAIDA_EMPRESTIMO and not texto and cliente is not None:
            texto = f'Empréstimo para {cliente.nome}'
        if len(texto) < 4:
            self.return_exception('A justificativa da saída manual é obrigatória.')
        if quantidade <= 0:
            self.return_exception('A quantidade deve ser maior que zero.')
        return texto

    def validar_conferencia(self, contagem, motivo):
        if contagem < 0:
            self.return_exception('O estoque físico não pode ser negativo.')
        texto = (motivo or '').strip()
        if len(texto) < 4:
            self.return_exception('É obrigatório justificar a conferência de inventário.')
        return texto

    def validar_delta(self, saldo_anterior, quantidade, tipo_saldo, nome_produto):
        saldo_novo = saldo_anterior + quantidade
        if saldo_novo < 0:
            if tipo_saldo == SALDO_SECO:
                return 0, -saldo_anterior
            rotulo = 'cheio' if tipo_saldo == SALDO_CHEIO else 'seco'
            raise BusinessRuleException(
                f'Saldo {rotulo} insuficiente de {nome_produto}. Disponível: {saldo_anterior}.'
            )
        return saldo_novo, quantidade
