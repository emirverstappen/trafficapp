from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Location, TrafficData

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')
    search_fields = ('name',)

@admin.register(TrafficData)
class TrafficDataAdmin(admin.ModelAdmin):
    list_display = ('location', 'timestamp', 'vehicle_count', 'person_count', 'get_congestion_level_display')
    list_filter = ('location', 'congestion_level', 'timestamp')
    date_hierarchy = 'timestamp'

# Override the default admin site
admin.site.site_header = 'Trafik Yoğunluk Analizi Admin'
admin.site.site_title = 'Trafik Yoğunluk Analizi Admin'
admin.site.index_title = 'Yönetim Paneli'

# Override the default "View site" link
admin.site.site_url = reverse('index')
