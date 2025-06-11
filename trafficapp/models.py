from django.db import models
from django.utils import timezone

class Location(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    def __str__(self):
        return self.name

class TrafficData(models.Model):
    CONGESTION_CHOICES = [
        ('calm', 'Sakin'),
        ('normal', 'Normal'),
        ('busy', 'Yoğun'),
        ('very_busy', 'Çok Yoğun'),
    ]
    
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='traffic_data')
    timestamp = models.DateTimeField(default=timezone.now)
    vehicle_count = models.IntegerField(default=0)
    person_count = models.IntegerField(default=0)
    congestion_level = models.CharField(max_length=10, choices=CONGESTION_CHOICES, default='normal')
    
    def __str__(self):
        return f"{self.location.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M')} - {self.get_congestion_level_display()}"
    
    class Meta:
        ordering = ['-timestamp']
