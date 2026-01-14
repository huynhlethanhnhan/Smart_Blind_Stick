from datetime import datetime
from app import db

class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    front_distance = db.Column(db.Float)
    left_distance = db.Column(db.Float)
    right_distance = db.Column(db.Float)
    ir_distance = db.Column(db.Float)
    mode = db.Column(db.Integer)
    wifi_strength = db.Column(db.Integer)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'front_distance': self.front_distance,
            'left_distance': self.left_distance,
            'right_distance': self.right_distance,
            'ir_distance': self.ir_distance,
            'mode': self.mode,
            'wifi_strength': self.wifi_strength
        }

class AlertHistory(db.Model):
    __tablename__ = 'alert_history'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    alert_type = db.Column(db.String(50))  # 'obstacle', 'hole', 'ground', 'low_battery'
    severity = db.Column(db.String(20))    # 'low', 'medium', 'high'
    distance = db.Column(db.Float)
    location = db.Column(db.String(50))    # 'front', 'left', 'right'
    resolved = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'alert_type': self.alert_type,
            'severity': self.severity,
            'distance': self.distance,
            'location': self.location,
            'resolved': self.resolved
        }

class DeviceStatus(db.Model):
    __tablename__ = 'device_status'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    device_id = db.Column(db.String(50), default='ESP32_001')
    power_status = db.Column(db.Boolean, default=False)
    battery_level = db.Column(db.Integer, default=100)
    wifi_connected = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'device_id': self.device_id,
            'power_status': self.power_status,
            'battery_level': self.battery_level,
            'wifi_connected': self.wifi_connected,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }