# Generated by Django 5.0 on 2024-01-08 15:11

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0002_alter_inventory_image"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="historicalinventory",
            name="date",
        ),
        migrations.AddField(
            model_name="historicalinventory",
            name="datetime",
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]