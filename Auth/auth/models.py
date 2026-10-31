import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def resumir_segredo(segredo: str) -> str:
    return hashlib.sha256(segredo.encode()).hexdigest()


class Sessao(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessoes',
    )
    chave_hash = models.CharField(max_length=64, unique=True)
    expira_em = models.DateTimeField()
    revogada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Sessão'
        verbose_name_plural = 'Sessões'

    @classmethod
    def abrir(cls, usuario):
        segredo = secrets.token_urlsafe(32)
        cls.objects.create(
            usuario=usuario,
            chave_hash=resumir_segredo(segredo),
            expira_em=timezone.now() + timedelta(seconds=settings.SESSAO_COOKIE_AGE),
        )
        return segredo

    @classmethod
    def revogar_segredo(cls, segredo: str) -> None:
        cls.objects.filter(
            chave_hash=resumir_segredo(segredo),
            revogada_em__isnull=True,
        ).update(revogada_em=timezone.now())

    @classmethod
    def buscar_ativa(cls, segredo: str):
        if not segredo:
            return None
        return (
            cls.objects.select_related('usuario')
            .filter(
                chave_hash=resumir_segredo(segredo),
                revogada_em__isnull=True,
                expira_em__gt=timezone.now(),
            )
            .first()
        )


class BloqueioLogin(models.Model):
    chave = models.CharField(max_length=200, unique=True)
    falhas = models.PositiveSmallIntegerField(default=0)
    bloqueado_ate = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Bloqueio de login'
        verbose_name_plural = 'Bloqueios de login'
