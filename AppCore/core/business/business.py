from AppCore.core.exceptions.exceptions import (
    AuthorizationException,
    BusinessRuleException,
    NotFoundException,
    ValidationException,
)


class ModelInstanceBusiness:
    exceptions_handled = (
        AuthorizationException,
        BusinessRuleException,
        ValidationException,
        NotFoundException,
    )

    def __init__(self, object_instance=None):
        self.object_instance = object_instance
