# Generated by Django 5.0.1 on 2025-05-18 14:53

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trafficapp', '0002_alter_trafficdata_congestion_level_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trafficdata',
            name='congestion_level',
            field=models.CharField(choices=[('calm', 'Sakin'), ('normal', 'Normal'), ('busy', 'Yoğun'), ('very_busy', 'Çok Yoğun')], default='normal', max_length=10),
        ),
        migrations.AlterField(
            model_name='trafficdata',
            name='location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='traffic_data', to='trafficapp.location'),
        ),
        migrations.AlterField(
            model_name='trafficdata',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
