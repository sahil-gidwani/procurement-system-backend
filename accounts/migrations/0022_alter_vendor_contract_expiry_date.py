# Generated by Django 4.2.10 on 2024-04-01 17:17

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0021_alter_vendor_contract_expiry_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vendor",
            name="contract_expiry_date",
            field=models.DateField(
                default=datetime.datetime(2029, 3, 31, 22, 47, 51, 341259)
            ),
        ),
    ]
