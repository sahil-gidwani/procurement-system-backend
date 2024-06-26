# Generated by Django 5.0 on 2024-02-19 13:17

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_user_gstin"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="gstin",
            field=models.CharField(
                max_length=15,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Enter a valid GSTIN (Goods and Services Tax Identification Number).",
                        regex="^\\d{2}[A-Z]{5}\\d{4}[A-Z]{1}\\d[Z]{1}[A-Z\\d]{1}$",
                    )
                ],
            ),
        ),
    ]
