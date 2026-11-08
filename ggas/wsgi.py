import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parent.parent)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ggas.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from ggas.backup_automatico import iniciar

iniciar()
