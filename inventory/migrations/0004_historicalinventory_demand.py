# Generated by Django 5.0 on 2024-01-26 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_remove_historicalinventory_date_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalinventory",
            name="demand",
            field=models.IntegerField(default=0),
        ),
    ]
