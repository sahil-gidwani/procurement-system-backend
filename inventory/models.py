from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MaxValueValidator, MinValueValidator
from accounts.models import User


class Inventory(models.Model):
    item_name = models.CharField(max_length=255)
    description = models.TextField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    location = models.CharField(max_length=255)
    date_added = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to="inventory", null=True, blank=True)
    procurement_officer = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.item_name)


class HistoricalInventory(models.Model):
    stock_quantity = models.IntegerField()
    demand = models.IntegerField(default=0)
    datetime = models.DateTimeField()
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.inventory.item_name} - {self.datetime}"


class OptimizedInventory(models.Model):
    demand = models.FloatField()
    ordering_cost = models.FloatField()
    holding_cost = models.FloatField()
    lead_time = models.IntegerField(null=True, blank=True)
    service_level = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], null=True, blank=True)
    safety_stock = models.FloatField(null=True, blank=True)
    reorder_point = models.FloatField(null=True, blank=True)
    shelf_life = models.IntegerField(null=True, blank=True)
    storage_limit = models.IntegerField(null=True, blank=True)
    eoq = models.FloatField(null=True, blank=True)
    inventory = models.OneToOneField(Inventory, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.inventory.item_name)


@receiver(post_save, sender=Inventory)
def create_historical_inventory(sender, instance, created, **kwargs):
    timestamp = instance.last_updated if not created else instance.date_added
    latest_historical_inventory = HistoricalInventory.objects.filter(
        inventory=instance
    ).order_by('-datetime').first()

    if latest_historical_inventory:
        demand = max(0, latest_historical_inventory.stock_quantity - instance.stock_quantity)
    else:
        demand = 0

    HistoricalInventory.objects.create(
        stock_quantity=instance.stock_quantity,
        datetime=timestamp,
        inventory=instance,
        demand=demand
    )
