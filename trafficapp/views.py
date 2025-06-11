from django.shortcuts import render, get_object_or_404, redirect
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import Location, TrafficData

import cv2
import numpy as np
import threading
import time
import folium
from folium.plugins import MarkerCluster
import json
import os
from pathlib import Path
from ultralytics import YOLO
import yt_dlp
import subprocess
import torch
import datetime

# Global variables
locations = {
    1: {
        'url': "https://www.youtube.com/watch?v=1EiC9bvVGnk",  # Wyoming Stream
        'lat': 43.479599,
        'lon': -110.762387,
        'name': "Jackson Town Square"
    },
    2: {
        'url': "https://www.youtube.com/watch?v=ByED80IKdIU",   # Michigan Park
        'lat': 41.940612,
        'lon': -85.000728,
        'name': "Four Corners Park"
    },
    3: {
        'url': "https://www.youtube.com/watch?v=hb22ynjZPxk",   # Chicago
        'lat': 41.781693,
        'lon': -87.762004,
        'name': "Chicago"
    },
    4: {
        'url': "https://www.youtube.com/watch?v=j9Sa4uBGGQ0",   # London
        'lat': 51.532014,
        'lon': -0.177332,
        'name': "London"
    }
}
current_location = 1
is_processing = False
processing_thread = None
frame_count = 0
vehicle_count = 0
person_count = 0
congestion_level = "Normal"

# Dictionary to store the last save time for each location {location_id: datetime_object}
last_save_time = {}

# Load YOLOv8 model
try:
    # Add safe globals for YOLO model loading
    torch.serialization.add_safe_globals(['ultralytics.nn.tasks.DetectionModel'])
    model = YOLO('yolov8n.pt')
    print("YOLO model başarıyla yüklendi")
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    model = None

def get_youtube_stream(location_id):
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(locations[location_id]['url'], download=False)
            return info['url']
    except Exception as e:
        print(f"Error getting YouTube stream: {e}")
        return None

def determine_congestion_level(vehicle_count, person_count,):
    area = 100
    density = (vehicle_count + person_count / 2) / area # Person count is weighted less
    if density < 0.05:
        return "Sakin"
    elif density < 0.08:
        return "Normal"
    elif density < 0.15:
        return "Yoğun"
    else:
        return "Çok Yoğun"

def get_congestion_color(level):
    if level == "Sakin":
        return "green"
    elif level == "Normal":
        return "blue"
    elif level == "Yoğun":
        return "yellow"
    else:  # Çok Yoğun
        return "red"

def process_video(location_id):
    global is_processing, frame_count, vehicle_count, person_count, congestion_level
    
    if location_id not in locations:
        return
    
    stream_url = get_youtube_stream(location_id)
    if not stream_url:
        return

    # FFmpeg command to get raw video stream
    command = [
        'ffmpeg',
        '-i', stream_url,
        '-f', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-vsync', '0',
        '-'
    ]

    pipe = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)
    
    # Get video dimensions
    cap = cv2.VideoCapture(stream_url)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    frame_size = width * height * 3

    while is_processing:
        try:
            raw_frame = pipe.stdout.read(frame_size)
            if len(raw_frame) != frame_size:
                print("Yayın bitti veya kare alınamadı.")
                break

            frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3))
            frame = frame.copy()  # Make frame writable

            # YOLO ile nesne tespiti
            results = model(frame, classes=[0, 2, 3, 5, 7], conf=0.5)
            temp_vehicle_count = 0
            temp_person_count = 0

            for result in results:
                boxes = result.boxes.cpu().numpy()
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].astype(int)
                    conf = box.conf[0]
                    cls = int(box.cls[0])
                    
                    if conf > 0.5:
                        if cls in [2, 3, 5, 7]:  # Araç sınıfları
                            color = (0, 0, 255)  # Kırmızı
                            label = "Vehicle"
                            temp_vehicle_count += 1
                        elif cls == 0:  # İnsan sınıfı
                            color = (0, 255, 0)  # Yeşil
                            label = "Person"
                            temp_person_count += 1
                        
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # İstatistikleri güncelle
            vehicle_count = temp_vehicle_count
            person_count = temp_person_count
            congestion_level = determine_congestion_level(vehicle_count, person_count)

            # İstatistikleri ekrana yazdır
            cv2.putText(frame, f"Vehicles: {vehicle_count}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(frame, f"Persons: {person_count}", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Congestion: {congestion_level}", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            # Frame'i JPEG formatına dönüştür
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        except Exception as e:
            print(f"Error processing frame: {e}")
            break

    pipe.stdout.close()
    pipe.wait()

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'trafficapp/login.html')

@login_required(login_url='login')
def index(request):
    # Ensure all locations exist in the database
    for loc_id, loc_data in locations.items():
        Location.objects.get_or_create(
            id=loc_id,
            defaults={
                'name': loc_data['name'],
                'latitude': loc_data['lat'],
                'longitude': loc_data['lon']
            }
        )
    
    # Get all locations (now guaranteed to exist)
    all_locations = Location.objects.all()
    
    # Create Folium map centered on the first location
    first_location = all_locations.order_by('id').first()
    m = folium.Map(
        location=[first_location.latitude, first_location.longitude],
        zoom_start=16,
        tiles='OpenStreetMap'
    )
    
    # Add markers for all locations with their congestion levels
    for location in all_locations:
        # Get the latest traffic data for this location
        latest_data = TrafficData.objects.filter(location=location).order_by('-timestamp').first()
        
        # Determine color based on congestion level (using Turkish string)
        color = get_congestion_color(latest_data.congestion_level if latest_data else "Normal")
        
        # Add marker
        folium.CircleMarker(
            location=[location.latitude, location.longitude],
            radius=31,
            popup=location.name,
            color=color,
            fill=True,
            fill_color=color
        ).add_to(m)
    
    # Save map to HTML
    map_html = m._repr_html_()
    
    # Prepare context for template
    context = {
        'locations': all_locations,
        'map_html': map_html,
        'selected_location': first_location.id if first_location else 1,
        'youtube_url': locations.get(first_location.id if first_location else 1, {}).get('url'),
    }
    
    return render(request, 'trafficapp/index.html', context)

@login_required(login_url='login')
def video_feed(request):
    global is_processing, processing_thread
    
    location_id = int(request.GET.get('location_id', 1))
    
    if not is_processing:
        is_processing = True
        processing_thread = threading.Thread(target=process_video, args=(location_id,))
        processing_thread.daemon = True
        processing_thread.start()
    
    return StreamingHttpResponse(
        process_video(location_id),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )

@login_required(login_url='login')
@csrf_exempt
def update_map(request):
    global vehicle_count, person_count, congestion_level, last_save_time
    
    location_id = int(request.GET.get('location_id', 1))
    
    # Kayıt yapma aralığı (saniye) - 10 dakika = 600 saniye
    save_interval = 600
    
    # Son kayıt zamanını kontrol et
    now = datetime.datetime.now()
    if location_id not in last_save_time or (now - last_save_time[location_id]).total_seconds() >= save_interval:
        try:
            # İlgili lokasyon objesini bul
            location_obj = Location.objects.get(pk=location_id)
            
            # Yeni TrafficData objesi oluştur ve kaydet
            TrafficData.objects.create(
                location=location_obj,
                timestamp=now,
                vehicle_count=vehicle_count,
                person_count=person_count,
                congestion_level=congestion_level
            )
            print(f"Traffic data saved for location {location_id} at {now}")
            
            # Son kayıt zamanını güncelle
            last_save_time[location_id] = now
            
        except Location.DoesNotExist:
            print(f"Location with id {location_id} does not exist.")
        except Exception as e:
            print(f"Error saving traffic data: {e}")
    
    # Get location data
    location_data = locations[location_id]
    
    # Create a map centered at the selected location
    m = folium.Map(
        location=[location_data['lat'], location_data['lon']],
        zoom_start=16, # Zoom in by 1 (15 + 1 = 16)
        tiles='OpenStreetMap'
    )
    
    # Add a marker for the current location with congestion level
    color = get_congestion_color(congestion_level)
    folium.CircleMarker(
        location=[location_data['lat'], location_data['lon']],
        radius=31, # Increase radius by 1 (30 + 1 = 31)
        popup=location_data['name'],
        color=color,
        fill=True,
        fill_color=color
    ).add_to(m)
    
    # Get the map HTML
    map_html = m._repr_html_()
    
    return JsonResponse({
        'vehicle_count': vehicle_count,
        'person_count': person_count,
        'congestion_level': congestion_level,
        'map_html': map_html
    })

def dashboard(request):
    return render(request, 'trafficapp/dashboard.html')

@login_required(login_url='login')
def wyoming(request):
    # Sadece konum 1 yayını ve index.html
    all_locations = Location.objects.all()
    first_location = all_locations.order_by('id').get(pk=1) # Sadece Wyoming (ID 1)
    m = folium.Map(
        location=[locations[1]['lat'], locations[1]['lon']],
        zoom_start=16,
        tiles='OpenStreetMap'
    )
    for location in all_locations:
        latest_data = TrafficData.objects.filter(location=location).order_by('-timestamp').first()
        color = get_congestion_color(latest_data.congestion_level if latest_data else "Normal")
        folium.CircleMarker(
            location=[location.latitude, location.longitude],
            radius=31,
            popup=location.name,
            color=color,
            fill=True,
            fill_color=color
        ).add_to(m)
    map_html = m._repr_html_()
    context = {
        'locations': all_locations,
        'map_html': map_html,
        'selected_location': 1,
        'youtube_url': locations[1]['url'],
    }
    return render(request, 'trafficapp/index_wyoming.html', context)

@login_required(login_url='login')
def michigan(request):
    # Sadece konum 2 yayını ve index_michigan.html
    all_locations = Location.objects.all()
    michigan_location = all_locations.order_by('id').get(pk=2) # Sadece Michigan (ID 2)
    m = folium.Map(
        location=[locations[2]['lat'], locations[2]['lon']],
        zoom_start=16,
        tiles='OpenStreetMap'
    )
    for location in all_locations:
        latest_data = TrafficData.objects.filter(location=location).order_by('-timestamp').first()
        color = get_congestion_color(latest_data.congestion_level if latest_data else "Normal")
        folium.CircleMarker(
            location=[location.latitude, location.longitude],
            radius=31,
            popup=location.name,
            color=color,
            fill=True,
            fill_color=color
        ).add_to(m)
    map_html = m._repr_html_()
    context = {
        'locations': all_locations,
        'map_html': map_html,
        'selected_location': 2,
        'youtube_url': locations[2]['url'],
    }
    return render(request, 'trafficapp/index_michigan.html', context)

@login_required(login_url='login')
def chicago(request):
    # Chicago için location_id=3
    all_locations = Location.objects.all()
    chicago_location = all_locations.order_by('id').get(pk=3) # Sadece Chicago (ID 3)
    m = folium.Map(
        location=[locations[3]['lat'], locations[3]['lon']],
        zoom_start=16,
        tiles='OpenStreetMap'
    )
    for location in all_locations:
        latest_data = TrafficData.objects.filter(location=location).order_by('-timestamp').first()
        color = get_congestion_color(latest_data.congestion_level if latest_data else "Normal")
        folium.CircleMarker(
            location=[location.latitude, location.longitude],
            radius=31,
            popup=location.name,
            color=color,
            fill=True,
            fill_color=color
        ).add_to(m)
    map_html = m._repr_html_()
    context = {
        'locations': all_locations,
        'map_html': map_html,
        'selected_location': 3,
        'youtube_url': locations[3]['url'],
    }
    return render(request, 'trafficapp/index_chicago.html', context)

@login_required(login_url='login')
def london(request):
    # London için location_id=4
    all_locations = Location.objects.all()
    london_location = all_locations.order_by('id').get(pk=4) # Sadece London (ID 4)
    m = folium.Map(
        location=[locations[4]['lat'], locations[4]['lon']],
        zoom_start=16,
        tiles='OpenStreetMap'
    )
    for location in all_locations:
        latest_data = TrafficData.objects.filter(location=location).order_by('-timestamp').first()
        color = get_congestion_color(latest_data.congestion_level if latest_data else "Normal")
        folium.CircleMarker(
            location=[location.latitude, location.longitude],
            radius=31,
            popup=location.name,
            color=color,
            fill=True,
            fill_color=color
        ).add_to(m)
    map_html = m._repr_html_()
    context = {
        'locations': all_locations,
        'map_html': map_html,
        'selected_location': 4,
        'youtube_url': locations[4]['url'],
    }
    return render(request, 'trafficapp/index_london.html', context)
