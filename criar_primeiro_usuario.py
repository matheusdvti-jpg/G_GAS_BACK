import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ggas.settings')
django.setup()

from django.core.management import call_command

from Colaboradores.colaboradores.management.commands.seed_inicial import EMAIL_ADMIN

call_command('seed_inicial')
print(f'E-mail: {EMAIL_ADMIN}')
