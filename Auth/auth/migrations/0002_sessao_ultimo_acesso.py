import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('auth_jwt', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sessao',
            name='ultimo_acesso',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
