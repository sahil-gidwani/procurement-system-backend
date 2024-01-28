from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MaxValueValidator, MinValueValidator


class User(AbstractUser):
    email = models.EmailField(unique=True)

    phone_number_regex = RegexValidator(
        regex=r"^\d{10}$", message="Phone number must be 10 digits."
    )
    phone_number = models.CharField(
        validators=[phone_number_regex], max_length=10, null=True
    )

    gstin_validator = RegexValidator(
        regex=r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1}$",
        message='Enter a valid GSTIN (Goods and Services Tax Identification Number).'
    )
    gstin = models.CharField(
        max_length=15,
        validators=[gstin_validator],
        unique=True
    )

    USER_ROLE_CHOICES = [
        ("procurement_officer", "Procurement Officer"),
        ("vendor", "Vendor"),
    ]
    user_role = models.CharField(max_length=255, choices=USER_ROLE_CHOICES)

    def __str__(self):
        return str(self.username)


class Vendor(models.Model):
    vendor_name = models.CharField(max_length=255)
    address = models.TextField()
    vendor_certified = models.BooleanField(default=False)

    VENDOR_TYPE_CHOICES = [
        ("supplier", "Supplier"),
        ("manufacturer", "Manufacturer"),
        ("service_provider", "Service Provider"),
    ]
    vendor_type = models.CharField(max_length=20, choices=VENDOR_TYPE_CHOICES)

    contract_expiry_date = models.DateField()
    vendor_rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.vendor_name)
