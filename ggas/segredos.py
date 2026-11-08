from django.core.exceptions import ImproperlyConfigured

CHAVE_SECRETA_PADRAO = 'ggas-dev-apenas-local-nao-usar-fora-desta-maquina'
CHAVE_SECRETA_EXEMPLO = 'troque-esta-chave-por-uma-com-pelo-menos-32-caracteres'
CHAVE_BANCO_EXEMPLO = 'troque-esta-chave-do-banco'


def recusar_segredo_publico(debug, em_teste, secret_key, db_key):
    """Com o debug desligado, o processo não sobe com segredo de exemplo."""
    if debug or em_teste:
        return
    if secret_key in ('', CHAVE_SECRETA_PADRAO, CHAVE_SECRETA_EXEMPLO):
        raise ImproperlyConfigured(
            'Com DJANGO_DEBUG desligado, defina DJANGO_SECRET_KEY diferente do padrão de desenvolvimento.'
        )
    if not db_key or db_key == CHAVE_BANCO_EXEMPLO:
        raise ImproperlyConfigured(
            'Com DJANGO_DEBUG desligado, defina DJANGO_DB_KEY diferente do exemplo.'
        )
