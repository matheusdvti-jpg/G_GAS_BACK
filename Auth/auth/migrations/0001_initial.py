from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Sessao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chave_hash', models.CharField(max_length=64, unique=True)),
                ('expira_em', models.DateTimeField()),
                ('revogada_em', models.DateTimeField(blank=True, null=True)),
                (
                    'usuario',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='sessoes',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                'verbose_name': 'Sessão',
                'verbose_name_plural': 'Sessões',
            },
        ),
        migrations.CreateModel(
            name='BloqueioLogin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chave', models.CharField(max_length=200, unique=True)),
                ('falhas', models.PositiveSmallIntegerField(default=0)),
                ('bloqueado_ate', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Bloqueio de login',
                'verbose_name_plural': 'Bloqueios de login',
            },
        ),
    ]
