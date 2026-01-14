from flask import jsonify, request
from app import app, db, socketio
from models import SensorData, AlertHistory, DeviceStatus
from datetime import datetime, timedelta
import json

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test API endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'Smart Cane API is working',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/data/receive', methods=['POST'])
def receive_data():
    """Receive data from ESP32"""
    try:
        data = request.json
        
        # Save sensor data
        sensor_data = SensorData(
            front_distance=data.get('front_distance', 0),
            left_distance=data.get('left_distance', 0),
            right_distance=data.get('right_distance', 0),
            ir_distance=data.get('ir_distance', 0),
            mode=data.get('mode', 1),
            wifi_strength=data.get('wifi_strength', -50)
        )
        db.session.add(sensor_data)
        
        # Update device status
        device_status = DeviceStatus(
            power_status=data.get('power_status', False),
            battery_level=data.get('battery_level', 100),
            wifi_connected=data.get('wifi_connected', False),
            last_seen=datetime.utcnow()
        )
        db.session.add(device_status)
        
        db.session.commit()
        
        # Prepare data for WebSocket
        ws_data = {
            'front_distance': sensor_data.front_distance,
            'left_distance': sensor_data.left_distance,
            'right_distance': sensor_data.right_distance,
            'ir_distance': sensor_data.ir_distance,
            'mode': sensor_data.mode,
            'power_status': device_status.power_status,
            'battery_level': device_status.battery_level,
            'wifi_connected': device_status.wifi_connected,
            'timestamp': sensor_data.timestamp.isoformat()
        }
        
        # Emit to WebSocket clients
        socketio.emit('sensor_update', ws_data)
        
        return jsonify({'status': 'success', 'message': 'Data received'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/statistics', methods=['GET'])
def get_statistics():
    """Get statistics for dashboard"""
    hours = request.args.get('hours', 24, type=int)
    time_limit = datetime.utcnow() - timedelta(hours=hours)
    
    # Get data from database
    data = SensorData.query.filter(
        SensorData.timestamp >= time_limit
    ).all()
    
    if not data:
        return jsonify({
            'avg_front': 0,
            'avg_left': 0,
            'avg_right': 0,
            'avg_ir': 0,
            'total_readings': 0
        })
    
    # Calculate statistics
    stats = {
        'avg_front': sum(d.front_distance for d in data) / len(data),
        'avg_left': sum(d.left_distance for d in data) / len(data),
        'avg_right': sum(d.right_distance for d in data) / len(data),
        'avg_ir': sum(d.ir_distance for d in data) / len(data),
        'total_readings': len(data),
        'time_period_hours': hours,
        'first_reading': data[0].timestamp.isoformat(),
        'last_reading': data[-1].timestamp.isoformat()
    }
    
    return jsonify(stats)

@app.route('/api/device/mode', methods=['POST'])
def set_device_mode():
    """Set device operating mode"""
    data = request.json
    mode = data.get('mode', 1)
    
    # Here you would typically send this to the ESP32
    # For now, we just log it
    print(f"Setting device mode to: {mode}")
    
    # Update current data
    from app import current_data
    current_data['mode'] = mode
    
    # Emit mode change
    socketio.emit('mode_change', {'mode': mode})
    
    return jsonify({'success': True, 'mode': mode})

@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Save system settings"""
    data = request.json
    
    # Save settings to database or file
    settings = {
        'danger_distance': data.get('danger_distance', 25),
        'warn_distance': data.get('warn_distance', 50),
        'safe_distance': data.get('safe_distance', 80),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    # Here you would typically save to database
    # For now, we just return the settings
    return jsonify({
        'success': True,
        'message': 'Settings saved',
        'settings': settings
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get system logs"""
    hours = request.args.get('hours', 24, type=int)
    time_limit = datetime.utcnow() - timedelta(hours=hours)
    
    logs = []
    
    # Get sensor data logs
    sensor_data = SensorData.query.filter(
        SensorData.timestamp >= time_limit
    ).order_by(SensorData.timestamp.desc()).limit(100).all()
    
    for data in sensor_data:
        logs.append({
            'type': 'sensor_data',
            'timestamp': data.timestamp.isoformat(),
            'message': f'Sensor data: F={data.front_distance}, L={data.left_distance}, R={data.right_distance}, IR={data.ir_distance}',
            'data': data.to_dict()
        })
    
    # Get alert logs
    alerts = AlertHistory.query.filter(
        AlertHistory.timestamp >= time_limit
    ).order_by(AlertHistory.timestamp.desc()).limit(50).all()
    
    for alert in alerts:
        logs.append({
            'type': 'alert',
            'timestamp': alert.timestamp.isoformat(),
            'message': f'Alert: {alert.alert_type} ({alert.severity}) at {alert.location}',
            'data': alert.to_dict()
        })
    
    # Sort logs by timestamp
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify(logs)