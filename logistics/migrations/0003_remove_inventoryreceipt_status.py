# Generated by Django 4.2.10 on 2024-04-01 10:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("logistics", "0002_remove_inventoryreceipt_inspection_report_url_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="inventoryreceipt",
            name="status",
        ),
    ]