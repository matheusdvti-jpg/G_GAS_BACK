from django.core.management.commands.runserver import Command as RunserverCommand

from ggas.preparar import preparar_banco


class Command(RunserverCommand):
    def handle(self, *args, **options):
        preparar_banco()
        super().handle(*args, **options)
