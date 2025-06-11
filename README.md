# Trafik Yoğunluk Analiz Uygulaması

Bu uygulama, gerçek zamanlı video analizi kullanarak trafik yoğunluğunu analiz eden bir web uygulamasıdır. YOLOv8 ve DeepSORT algoritmalarını kullanarak kişi ve araç tespiti yapar, ve Folium haritaları üzerinde yoğunluk bilgilerini görselleştirir.

## Özellikler

- Gerçek zamanlı video analizi
- YOLOv8 ile kişi ve araç tespiti
- DeepSORT ile nesne takibi
- Yoğunluk seviyesi hesaplama
- Folium haritaları ile görselleştirme
- Bootstrap ile modern ve duyarlı arayüz
- Çoklu konum desteği

## Gereksinimler

- Python 3.8+
- Django 4.2+
- OpenCV
- YOLOv8
- DeepSORT
- Folium
- NumPy
- Pillow

## Kurulum

1. Projeyi klonlayın:
```bash
git clone https://github.com/emirverstappen/trafficapp.git
cd traffic-analysis-app
```

2. Sanal ortam oluşturun ve aktifleştirin:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Gereksinimleri yükleyin:
```bash
pip install -r requirements.txt
```

4. Veritabanı migrasyonlarını yapın:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Süper kullanıcı oluşturun:
```bash
python manage.py createsuperuser
```

6. Sunucuyu başlatın:
```bash
python manage.py runserver
```

## Kullanım

1. Tarayıcınızda `http://localhost:8000` adresine gidin
2. Dropdown menüden bir konum seçin
3. Video akışı otomatik olarak başlayacak ve analiz edilecektir
4. Yoğunluk bilgileri ve harita otomatik olarak güncellenecektir

## Yapılandırma

- Konumları admin panelinden (`/admin`) yönetebilirsiniz
- Her konum için enlem ve boylam değerlerini ayarlayabilirsiniz
- Yoğunluk seviyeleri otomatik olarak hesaplanır

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın. 