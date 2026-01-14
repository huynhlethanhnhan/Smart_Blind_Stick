import requests
import time
from datetime import datetime, timedelta
from config import Config

def format_timestamp(timestamp):
    """Format timestamp to readable string"""
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    return timestamp.strftime('%H:%M:%S %d/%m/%Y')

def calculate_distance_category(distance):
    """Categorize distance for display"""
    if distance == 0 or distance >= 300:
        return 'none'
    elif distance < 25:
        return 'danger'
    elif distance < 50:
        return 'warning'
    else:
        return 'safe'

def get_alert_icon(alert_type, severity):
    """Get appropriate icon for alert type"""
    icons = {
        'obstacle': {
            'high': 'bi-exclamation-octagon',
            'medium': 'bi-exclamation-triangle',
            'low': 'bi-info-circle'
        },
        'hole': 'bi-exclamation-triangle',
        'ground': 'bi-info-circle',
        'battery': 'bi-battery-half'
    }
    
    if alert_type in icons:
        if isinstance(icons[alert_type], dict):
            return icons[alert_type].get(severity, 'bi-exclamation-triangle')
        return icons[alert_type]
    
    return 'bi-exclamation-triangle'

def get_wifi_strength_icon(rssi):
    """Get WiFi strength icon based on RSSI"""
    if rssi >= -50:
        return 'bi-wifi', 'text-success'
    elif rssi >= -70:
        return 'bi-wifi', 'text-warning'
    else:
        return 'bi-wifi-1', 'text-danger'

def send_push_notification(title, message, alert_type='info'):
    """Send push notification (can be extended for mobile apps)"""
    # This is a placeholder for push notification service
    print(f"Push Notification - {alert_type.upper()}: {title} - {message}")
    
    # Example: Integrate with Firebase Cloud Messaging
    # fcm_url = 'https://fcm.googleapis.com/fcm/send'
    # headers = {'Authorization': 'key=YOUR_FCM_KEY'}
    # data = {
    #     'to': '/topics/smart_cane',
    #     'notification': {'title': title, 'body': message}
    # }
    # response = requests.post(fcm_url, json=data, headers=headers)
    # return response.status_code == 200

def validate_sensor_data(data):
    """Validate sensor data before processing"""
    required_fields = ['front_distance', 'left_distance', 'right_distance', 'ir_distance']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"
        
        value = data[field]
        if not isinstance(value, (int, float)):
            return False, f"Invalid type for {field}: {type(value)}"
        
        if value < 0 or value > 1000:
            return False, f"Invalid range for {field}: {value}"
    
    return True, "Data valid"

def calculate_statistics(data_points):
    """Calculate statistics from data points"""
    if not data_points:
        return {}
    
    stats = {
        'count': len(data_points),
        'avg_front': sum(d['front_distance'] for d in data_points) / len(data_points),
        'avg_left': sum(d['left_distance'] for d in data_points) / len(data_points),
        'avg_right': sum(d['right_distance'] for d in data_points) / len(data_points),
        'avg_ir': sum(d['ir_distance'] for d in data_points) / len(data_points),
        'min_front': min(d['front_distance'] for d in data_points),
        'max_front': max(d['front_distance'] for d in data_points),
        'last_update': data_points[-1]['timestamp'] if 'timestamp' in data_points[-1] else None
    }
    
    return stats