from datetime import datetime

from AppCore.core.exceptions.exceptions import ValidationException
from AppCore.core.rules.rules import ModelInstanceRules


class LeituraRules(ModelInstanceRules):
    def interpretar_data(self, valor):
        if not valor:
            return None
        try:
            return datetime.strptime(valor, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationException('Use datas no formato AAAA-MM-DD.')

    def validar_periodo(self, inicio, fim):
        if (inicio is None) != (fim is None):
            raise ValidationException('Informe as duas datas do período, de e até.')
        if inicio and fim and inicio > fim:
            self.return_exception('A data inicial não pode ser posterior à data final.')
        return True
