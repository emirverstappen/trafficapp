// Main JavaScript file for Traffic Analysis App

// Function to handle video feed errors
function handleVideoError() {
    const videoFeed = document.getElementById('video-feed');
    if (videoFeed) {
        videoFeed.onerror = function() {
            this.src = '/static/img/error.png';
            alert('Video akışı başlatılamadı. Lütfen kamera erişimini kontrol edin.');
        };
    }
}

// Function to handle location change
function handleLocationChange() {
    const locationSelect = document.getElementById('location-select');
    if (locationSelect) {
        locationSelect.addEventListener('change', function() {
            const locationId = this.value;
            updateVideoFeed(locationId);
            updateMapAndStats(locationId);
        });
    }
}

// Function to update video feed
function updateVideoFeed(locationId) {
    const videoFeed = document.getElementById('video-feed');
    if (videoFeed) {
        videoFeed.src = `/video_feed/?location_id=${locationId}`;
    }
}

// Function to update map and stats
function updateMapAndStats(locationId) {
    $.ajax({
        url: '/update_map/',
        data: {
            location_id: locationId
        },
        success: function(data) {
            // Update map
            $('#map-container').html(data.map_html);
            
            // Update stats
            $('#vehicle-count').text(data.vehicle_count);
            $('#person-count').text(data.person_count);
            
            // Update congestion level
            updateCongestionLevel(data.congestion_level);
        },
        error: function() {
            console.error('Failed to update map and stats');
        }
    });
}

// Function to update congestion level
function updateCongestionLevel(level) {
    const congestionLevel = document.getElementById('congestion-level');
    const congestionCard = document.getElementById('congestion-card');
    
    if (congestionLevel && congestionCard) {
        let text = 'Normal';
        let className = 'congestion-normal';
        
        switch(level) {
            case 'calm':
                text = 'Sakin';
                className = 'congestion-calm';
                break;
            case 'normal':
                text = 'Normal';
                className = 'congestion-normal';
                break;
            case 'busy':
                text = 'Yoğun';
                className = 'congestion-busy';
                break;
            case 'very_busy':
                text = 'Çok Yoğun';
                className = 'congestion-very-busy';
                break;
        }
        
        congestionLevel.textContent = text;
        
        // Remove all congestion classes and add the current one
        congestionCard.classList.remove('congestion-calm', 'congestion-normal', 'congestion-busy', 'congestion-very-busy');
        congestionCard.classList.add(className);
    }
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    handleVideoError();
    handleLocationChange();
    
    // Update map and stats every 5 seconds
    setInterval(function() {
        const locationId = document.getElementById('location-select').value;
        updateMapAndStats(locationId);
    }, 5000);
}); 