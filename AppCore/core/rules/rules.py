from AppCore.core.exceptions.exceptions import BusinessRuleException


class ModelInstanceRules:
    def __init__(self, object_instance=None):
        self.object_instance = object_instance

    def return_exception(self, message='', details=None):
        raise BusinessRuleException(message, details)

    def return_not_allowed(self):
        return False

    def return_response(self, message='', details=None, execute_exception=False):
        if execute_exception:
            self.return_exception(message, details)
        return False
