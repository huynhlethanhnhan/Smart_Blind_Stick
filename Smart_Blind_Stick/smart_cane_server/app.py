from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
import threading
import time

app = Flask(__name__)
CORS(app)  # Cho phép ESP32 kết nối

# ============================================
# BIẾN TOÀN CỤC
# ============================================
current_data = {
    'front_distance': 0,
    'left_distance': 0,
    'right_distance': 0,
    'ir_distance': 0,
    'mode': 1,
    'power_status': False,
    'battery_level': 100,
    'wifi_connected': False,
    'last_update': None,
    'alerts': []
}

data_history = []
system_settings = {
    'danger_distance': 25,
    'warn_distance': 50,
    'safe_distance': 80,
    'ir_ground': 20,
    'ir_hole': 40
}

# File lưu trữ
DATA_FILE = 'data.json'
SETTINGS_FILE = 'settings.json'

# ============================================
# HÀM TIỆN ÍCH
# ============================================
def load_data():
    """Tải dữ liệu từ file"""
    global data_history, system_settings
    
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data_history = json.load(f)
                print(f"📂 Đã tải {len(data_history)} bản ghi từ file")
    except Exception as e:
        print(f"❌ Lỗi khi tải data.json: {e}")
        data_history = []
    
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                system_settings.update(json.load(f))
    except Exception as e:
        print(f"❌ Lỗi khi tải settings.json: {e}")
        pass

def save_data():
    """Lưu dữ liệu vào file"""
    try:
        # Chỉ lưu 1000 bản ghi gần nhất
        recent_history = data_history[-1000:] if len(data_history) > 1000 else data_history
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(recent_history, f, ensure_ascii=False, indent=2)
            print(f"💾 Đã lưu {len(recent_history)} bản ghi vào data.json")
            
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(system_settings, f, ensure_ascii=False, indent=2)
            print("⚙️ Đã lưu cài đặt vào settings.json")
            
    except Exception as e:
        print(f"❌ Lỗi khi lưu dữ liệu: {e}")

def check_alerts(data):
    """Kiểm tra cảnh báo từ dữ liệu sensor"""
    alerts = []
    
    # Chướng ngại vật phía trước
    if 0 < data['front_distance'] < system_settings['danger_distance']:
        alerts.append({
            'type': 'danger',
            'message': f'⚠️ CHƯỚNG NGẠI VẬT PHÍA TRƯỚC: {data["front_distance"]}cm',
            'location': 'front',
            'timestamp': datetime.now().isoformat()
        })
    elif system_settings['danger_distance'] <= data['front_distance'] < system_settings['warn_distance']:
        alerts.append({
            'type': 'warning',
            'message': f'⚠️ Cảnh báo phía trước: {data["front_distance"]}cm',
            'location': 'front',
            'timestamp': datetime.now().isoformat()
        })
    
    # Bên trái
    if 0 < data['left_distance'] < system_settings['warn_distance']:
        alerts.append({
            'type': 'warning',
            'message': f'⚠️ Có vật thể bên trái: {data["left_distance"]}cm',
            'location': 'left',
            'timestamp': datetime.now().isoformat()
        })
    
    # Bên phải
    if 0 < data['right_distance'] < system_settings['warn_distance']:
        alerts.append({
            'type': 'warning',
            'message': f'⚠️ Có vật thể bên phải: {data["right_distance"]}cm',
            'location': 'right',
            'timestamp': datetime.now().isoformat()
        })
    
    # Cảm biến IR
    if data['ir_distance'] < system_settings['ir_ground']:
        alerts.append({
            'type': 'info',
            'message': '⚠️ Mặt đất không bằng phẳng',
            'location': 'bottom',
            'timestamp': datetime.now().isoformat()
        })
    elif data['ir_distance'] > system_settings['ir_hole']:
        alerts.append({
            'type': 'danger',
            'message': f'⚠️ CÓ HỐ/BẬC THỀM: {data["ir_distance"]}cm',
            'location': 'bottom',
            'timestamp': datetime.now().isoformat()
        })
    
    return alerts

def auto_save():
    """Tự động lưu dữ liệu mỗi 5 phút"""
    while True:
        time.sleep(300)  # 5 phút
        if data_history:
            save_data()

# ============================================
# ROUTES - API
# ============================================
@app.route('/')
def index():
    """Trang chủ dashboard"""
    return render_template('index.html')

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test server"""
    return jsonify({
        'success': True,
        'message': '✅ Server đang hoạt động!',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0'
    })

@app.route('/api/data/current', methods=['GET'])
def get_current_data():
    """Lấy dữ liệu hiện tại"""
    return jsonify({
        'success': True,
        'data': current_data,
        'settings': system_settings,
        'history_count': len(data_history),
        'server_time': datetime.now().isoformat()
    })

@app.route('/api/data/receive', methods=['POST'])
def receive_data():
    """Nhận dữ liệu từ ESP32"""
    try:
        print(f"\n{'='*60}")
        print(f"📥 [{datetime.now().strftime('%H:%M:%S')}] NHẬN DỮ LIỆU TỪ ESP32")
        print(f"{'='*60}")
        
        if not request.is_json:
            print("❌ Không phải JSON format")
            print(f"Raw data: {request.data}")
            return jsonify({'success': False, 'error': 'Invalid JSON'}), 400
        
        data = request.get_json()
        print(f"📊 Dữ liệu nhận được:")
        print(json.dumps(data, indent=2))
        
        # Cập nhật dữ liệu hiện tại
        current_data.update({
            'front_distance': float(data.get('front_distance', 0)),
            'left_distance': float(data.get('left_distance', 0)),
            'right_distance': float(data.get('right_distance', 0)),
            'ir_distance': float(data.get('ir_distance', 0)),
            'mode': int(data.get('mode', 1)),
            'power_status': bool(data.get('power_status', False)),
            'battery_level': int(data.get('battery_level', 100)),
            'wifi_connected': bool(data.get('wifi_connected', False)),
            'last_update': datetime.now().isoformat()
        })
        
        # Kiểm tra cảnh báo
        current_data['alerts'] = check_alerts(current_data)
        
        # Thêm vào lịch sử
        history_entry = {
            'timestamp': current_data['last_update'],
            'front_distance': current_data['front_distance'],
            'left_distance': current_data['left_distance'],
            'right_distance': current_data['right_distance'],
            'ir_distance': current_data['ir_distance'],
            'mode': current_data['mode'],
            'alerts': current_data['alerts']
        }
        
        data_history.append(history_entry)
        
        print(f"\n✅ Đã cập nhật:")
        print(f"   📏 Trước: {current_data['front_distance']}cm")
        print(f"   📏 Trái: {current_data['left_distance']}cm")
        print(f"   📏 Phải: {current_data['right_distance']}cm")
        print(f"   📏 IR: {current_data['ir_distance']}cm")
        print(f"   ⚙️ Chế độ: {current_data['mode']}")
        print(f"   🔌 Nguồn: {'BẬT' if current_data['power_status'] else 'TẮT'}")
        print(f"   📶 WiFi: {'KẾT NỐI' if current_data['wifi_connected'] else 'MẤT KẾT NỐI'}")
        print(f"   ⚠️ Cảnh báo: {len(current_data['alerts'])}")
        print(f"{'='*60}")
        
        # Tự động lưu sau 10 bản ghi
        if len(data_history) % 10 == 0:
            save_data()
        
        return jsonify({
            'success': True,
            'message': 'Dữ liệu đã nhận',
            'alerts': len(current_data['alerts']),
            'timestamp': current_data['last_update']
        })
        
    except Exception as e:
        print(f"❌ LỖI: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data/history', methods=['GET'])
def get_history():
    """Lấy lịch sử dữ liệu"""
    hours = request.args.get('hours', 24, type=int)
    
    if hours <= 0:
        return jsonify({'success': False, 'message': 'Thời gian không hợp lệ'})
    
    time_limit = datetime.now() - timedelta(hours=hours)
    
    filtered_history = [
        entry for entry in data_history 
        if datetime.fromisoformat(entry['timestamp']) > time_limit
    ]
    
    filtered_history = filtered_history[-100:]  # Giới hạn 100 bản ghi
    
    return jsonify({
        'success': True,
        'count': len(filtered_history),
        'data': filtered_history
    })

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Lấy cảnh báo gần đây"""
    hours = request.args.get('hours', 6, type=int)
    time_limit = datetime.now() - timedelta(hours=hours)
    
    all_alerts = []
    for entry in data_history:
        if datetime.fromisoformat(entry['timestamp']) > time_limit:
            all_alerts.extend(entry.get('alerts', []))
    
    all_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    all_alerts = all_alerts[:50]
    
    return jsonify({
        'success': True,
        'count': len(all_alerts),
        'alerts': all_alerts
    })

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    """Lấy/cập nhật cài đặt"""
    if request.method == 'POST':
        try:
            new_settings = request.json
            system_settings.update(new_settings)
            save_data()
            
            return jsonify({
                'success': True,
                'message': 'Cài đặt đã lưu',
                'settings': system_settings
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Lỗi: {str(e)}'
            }), 500
    
    # GET request
    return jsonify({
        'success': True,
        'settings': system_settings
    })

@app.route('/api/device/mode', methods=['POST'])
def set_mode():
    """Thay đổi chế độ"""
    try:
        data = request.json
        mode = data.get('mode', 1)
        
        current_data['mode'] = mode
        
        return jsonify({
            'success': True,
            'message': f'Đã đổi sang chế độ {mode}',
            'mode': mode
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500

@app.route('/api/system/info', methods=['GET'])
def system_info():
    """Thông tin hệ thống"""
    return jsonify({
        'success': True,
        'system': {
            'name': 'Gậy Thông Minh - Server',
            'version': '1.0',
            'data_points': len(data_history),
            'last_update': current_data['last_update'],
            'server_time': datetime.now().isoformat()
        }
    })

@app.route('/api/system/clear', methods=['POST'])
def clear_data():
    """Xóa dữ liệu cũ"""
    try:
        global data_history
        data_history = data_history[-100:]  # Giữ 100 bản ghi gần nhất
        
        save_data()
        
        return jsonify({
            'success': True,
            'message': 'Đã xóa dữ liệu cũ, giữ lại 100 bản ghi gần nhất',
            'remaining': len(data_history)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        }), 500

# ============================================
# CHẠY SERVER
# ============================================
if __name__ == '__main__':
    # Tải dữ liệu từ file
    load_data()
    
    print(f"\n{'='*60}")
    print(f"🚀 SERVER GẬY THÔNG MINH")
    print(f"{'='*60}")
    print(f"📂 Dữ liệu: {len(data_history)} bản ghi")
    print(f"⚙️ Ngưỡng nguy hiểm: {system_settings['danger_distance']}cm")
    print(f"⚙️ Ngưỡng cảnh báo: {system_settings['warn_distance']}cm")
    print(f"🌐 Địa chỉ local: http://localhost:5000")
    # print(f"🌐 Địa chỉ LAN: http://{get_local_ip()}:5000")
    print(f"📡 Chờ dữ liệu từ ESP32...")
    print(f"💾 Tự động lưu: Mỗi 5 phút")
    print(f"{'='*60}\n")
    
    # Khởi động thread tự động lưu
    save_thread = threading.Thread(target=auto_save, daemon=True)
    save_thread.start()
    
    # Chạy server
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

def get_local_ip():
    """Lấy IP local của máy"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"