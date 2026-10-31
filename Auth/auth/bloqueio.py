from datetime import timedelta

from django.utils import timezone

from .models import BloqueioLogin

LIMITE_FALHAS = 5
MINUTOS_BLOQUEIO = 15


def chave_de(ip: str, identificador: str) -> str:
    return f'{ip}|{(identificador or "").strip().lower()}'[:200]


def bloqueado_ate(chave: str):
    registro = BloqueioLogin.objects.filter(chave=chave).first()
    if registro is None or registro.bloqueado_ate is None:
        return None
    if registro.bloqueado_ate <= timezone.now():
        registro.falhas = 0
        registro.bloqueado_ate = None
        registro.save(update_fields=['falhas', 'bloqueado_ate'])
        return None
    return registro.bloqueado_ate


def registrar_falha(chave: str) -> None:
    registro, _criado = BloqueioLogin.objects.get_or_create(chave=chave)
    agora = timezone.now()
    if registro.bloqueado_ate and registro.bloqueado_ate <= agora:
        registro.falhas = 0
        registro.bloqueado_ate = None
    registro.falhas += 1
    if registro.falhas >= LIMITE_FALHAS:
        registro.bloqueado_ate = agora + timedelta(minutes=MINUTOS_BLOQUEIO)
        registro.falhas = 0
    registro.save()


def limpar(chave: str) -> None:
    BloqueioLogin.objects.filter(chave=chave).delete()
