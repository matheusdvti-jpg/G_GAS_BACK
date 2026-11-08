from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import BloqueioLogin

LIMITE_FALHAS = 5
MINUTOS_BLOQUEIO = 15


def chave_de(ip: str, identificador: str) -> str:
    return f'{ip}|{(identificador or "").strip().lower()}'[:200]


def bloqueado_ate(chave: str):
    with transaction.atomic():
        registro = BloqueioLogin.objects.select_for_update().filter(chave=chave).first()
        if registro is None or registro.bloqueado_ate is None:
            return None
        if registro.bloqueado_ate <= timezone.now():
            registro.falhas = 0
            registro.bloqueado_ate = None
            registro.save(update_fields=['falhas', 'bloqueado_ate'])
            return None
        return registro.bloqueado_ate


def registrar_falha(chave: str) -> bool:
    agora = timezone.now()
    with transaction.atomic():
        registro, _criado = BloqueioLogin.objects.select_for_update().get_or_create(
            chave=chave,
            defaults={'falhas': 0, 'bloqueado_ate': None},
        )
        if registro.bloqueado_ate and registro.bloqueado_ate <= agora:
            registro.falhas = 0
            registro.bloqueado_ate = None
        registro.falhas += 1
        bloqueou = False
        if registro.falhas >= LIMITE_FALHAS:
            registro.bloqueado_ate = agora + timedelta(minutes=MINUTOS_BLOQUEIO)
            registro.falhas = 0
            bloqueou = True
        registro.save(update_fields=['falhas', 'bloqueado_ate'])
        return bloqueou


def limpar(chave: str) -> None:
    BloqueioLogin.objects.filter(chave=chave).delete()
