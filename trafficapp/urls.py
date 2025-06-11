from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('wyoming/', views.wyoming, name='wyoming'),
    path('michigan/', views.michigan, name='michigan'),
    path('chicago/', views.chicago, name='chicago'),
    path('london/', views.london, name='london'),
    path('index/', views.index, name='index'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('update_map/', views.update_map, name='update_map'),
]
