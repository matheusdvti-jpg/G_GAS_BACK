import os

from django.core.management import call_command


def preparar_banco():
    """Aplica as migrações e garante o administrador inicial antes do servidor subir."""
    if os.environ.get('RUN_MAIN') == 'true':
        return
    call_command('migrate', interactive=False, verbosity=1)
    call_command('seed_inicial')
