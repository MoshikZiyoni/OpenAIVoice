# Generated by Django 4.2.9 on 2025-04-04 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('callAPI', '0009_alter_call_direction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='call',
            name='call_sid',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
