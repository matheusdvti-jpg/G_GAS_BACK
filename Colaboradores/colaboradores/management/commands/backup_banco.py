from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ggas.db.sqlite_cifrado.base import copiar_banco_cifrado


class Command(BaseCommand):
    help = (
        'Copia o banco cifrado para backups/db.sqlite3.bak. '
        'A cópia nova só substitui a anterior quando a gravação termina.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--destino',
            default='',
            help='Arquivo do backup. O padrão é backups/db.sqlite3.bak.',
        )
        parser.add_argument(
            '--origem',
            default='',
            help='Arquivo do banco. O padrão é o banco configurado no projeto.',
        )

    def handle(self, *args, **options):
        config = settings.DATABASES['default']
        origem = options['origem'] or str(config.get('NAME') or '')
        segredo = config.get('PASSWORD') or ''
        destino = options['destino'] or str(Path(settings.BASE_DIR) / 'backups' / 'db.sqlite3.bak')
        try:
            copiar_banco_cifrado(origem, destino, segredo)
        except Exception as erro:
            raise CommandError(
                f'O backup não foi concluído. A cópia anterior foi mantida. {erro}'
            ) from erro
        self.stdout.write(self.style.SUCCESS(f'Backup gravado em {destino}.'))
