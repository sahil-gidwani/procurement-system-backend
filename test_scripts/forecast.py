import os
import django
import numpy as np
from datetime import timedelta

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "procurement_system_backend.settings")
django.setup()

from django.utils import timezone
from inventory.models import HistoricalInventory, Inventory

# Get an inventory object (replace 4 with the appropriate ID)
inventory_obj = Inventory.objects.get(pk=5)

# Define the number of weeks (2 years = 104 weeks)
num_weeks = 260

# Define the start and end dates for the past 2 years
end_date = timezone.now()
start_date = end_date - timedelta(weeks=num_weeks)

# Define seasonal parameters
amplitude = 50  # Amplitude of the seasonal variation
frequency = 52  # Weekly frequency for seasonal variation (1 year)

# Define noise parameters
noise_mean = 0
noise_std = 10  # Adjust the standard deviation based on the desired level of randomness

# Define trend parameters
trend_slope = 0.5  # Slope of the trend component

# Generate and insert data into HistoricalInventory for every week
for i in range(num_weeks):
    # Calculate the datetime for the current week
    current_date = start_date + timedelta(weeks=i)

    # Generate demand using a sine wave function for seasonal variation
    demand = amplitude * np.sin(2 * np.pi * i / frequency)

    # Add a linear trend component
    demand += trend_slope * i

    # Introduce randomness by adding a random noise component
    random_noise = np.random.normal(noise_mean, noise_std)
    demand += random_noise

    # Ensure demand is non-negative
    if demand < 0:
        demand = 0

    # For simplicity, let's assume a constant stock quantity
    stock_quantity = 100

    # Create HistoricalInventory instance and save to the database
    HistoricalInventory.objects.create(
        stock_quantity=stock_quantity,
        demand=demand,
        datetime=current_date,
        inventory=inventory_obj,
    )

print(
    f"{num_weeks} weeks of seasonal data with trend and randomness inserted into HistoricalInventory."
)
