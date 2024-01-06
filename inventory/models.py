from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User


class Inventory(models.Model):
    item_name = models.CharField(max_length=255)
    description = models.TextField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    reorder_level = models.IntegerField()
    location = models.CharField(max_length=255)
    date_added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    expiration_date = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to="inventory", null=True, blank=True)
    procurement_officer = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.item_name)


class HistoricalInventory(models.Model):
    stock_quantity = models.IntegerField()
    date = models.DateField()
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.inventory.item_name} - {self.date}"


@receiver(post_save, sender=Inventory)
def create_historical_inventory(sender, instance, created, **kwargs):
    timestamp = instance.last_updated if not created else instance.date_added

    HistoricalInventory.objects.create(
        stock_quantity=instance.stock_quantity, date=timestamp, inventory=instance
    )
