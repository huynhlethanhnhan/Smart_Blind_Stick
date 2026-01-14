#include <Wire.h>
#include <U8g2lib.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ThingSpeak.h>
#include "config.h"

// ============================================
// OLED Object
// ============================================
U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE);

// ============================================
// CẤU HÌNH MẠNG - THAY ĐỔI Ở ĐÂY
// ============================================
const char *WIFI_SSID = "NTTU-NHT";                                         // Tên WiFi của bạn
const char *WIFI_PASSWORD = "";                                // Mật khẩu WiFi
const char *SERVER_URL = "http://172.16.241.253:5000/api/data/receive"; // IP server Flask

// ThingSpeak Configuration
unsigned long THINGSPEAK_CHANNEL = 3226411;
const char *THINGSPEAK_API_KEY = "J7LN6D5XO1QC9E6O";

// ============================================
// HẰNG SỐ HỆ THỐNG
// ============================================
const int DANGER_DIST = 25;
const int WARN_DIST = 50;
const int SAFE_DIST = 80;
const int IR_GROUND = 20;
const int IR_HOLE = 40;
const long SEND_INTERVAL = 15000;

// ============================================
// BIẾN TOÀN CỤC
// ============================================
bool powerOn = false;
int currentMode = 1;
bool lastPowerState = HIGH;
bool lastModeState = HIGH;
unsigned long lastSendTime = 0;
unsigned long lastServerSend = 0;
unsigned long lastDebugTime = 0;

int frontDist = 999, leftDist = 999, rightDist = 999;
int irValue = 0;
int irDistance = 0;

WiFiClient client;

// ============================================
// ICON BITMAPS
// ============================================
const unsigned char icon_up[] = {0b00011000, 0b00111100, 0b01111110, 0b11111111, 0b00011000, 0b00011000, 0b00011000, 0b00000000};
const unsigned char icon_down[] = {0b00011000, 0b00011000, 0b00011000, 0b11111111, 0b01111110, 0b00111100, 0b00011000, 0b00000000};
const unsigned char icon_left[] = {0b00010000, 0b00110000, 0b01111111, 0b11111111, 0b01111111, 0b00110000, 0b00010000, 0b00000000};
const unsigned char icon_right[] = {0b00001000, 0b00001100, 0b11111110, 0b11111111, 0b11111110, 0b00001100, 0b00001000, 0b00000000};
const unsigned char icon_warning[] = {0b00011000, 0b00011000, 0b00011000, 0b00011000, 0b00011000, 0b00000000, 0b00011000, 0b00000000};
const unsigned char icon_error[] = {0b11000011, 0b11100111, 0b01111110, 0b00111100, 0b00111100, 0b01111110, 0b11100111, 0b11000011};
const unsigned char icon_ok[] = {0b00000001, 0b00000011, 0b00000110, 0b10001100, 0b11011000, 0b01110000, 0b00100000, 0b00000000};
const unsigned char icon_ground[] = {0b11111111, 0b11111111, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000, 0b00000000};
const unsigned char icon_hole[] = {0b00111100, 0b01000010, 0b10000001, 0b10000001, 0b10000001, 0b10000001, 0b01000010, 0b00111100};

// ============================================
// KHAI BÁO HÀM
// ============================================
void setupPins();
void checkButtons();
void readSensors();
int getDistance(int trig, int echo);
void processSensorMode();
void processAlertMode();
void showWelcomeScreen();
void showSleepScreen();
void showBootScreen();
void showModeScreen();
void displayOLEDWithIcons();
void setRGB(int r, int g, int b);
void powerOnEffect();
void powerOffEffect();
void connectToWiFi();
void uploadToCloud();
void scanWiFiNetworks();
void sendToServer();
void debugInfo();

// ============================================
// HÀM GỬI DỮ LIỆU LÊN SERVER FLASK
// ============================================
void sendToServer()
{
    // Kiểm tra WiFi
    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println("[SERVER] ❌ WiFi không kết nối");
        return;
    }

    // Kiểm tra nguồn
    if (!powerOn)
    {
        return;
    }

    HTTPClient http;

    Serial.println("\n[SERVER] 📤 Đang gửi dữ liệu...");

    // Tạo URL
    String url = String(SERVER_URL);
    Serial.print("[SERVER] URL: ");
    Serial.println(url);

    // Khởi tạo kết nối
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(5000); // Timeout 5 giây

    // Tạo JSON data
    String jsonData = "{";
    jsonData += "\"front_distance\":" + String(frontDist) + ",";
    jsonData += "\"left_distance\":" + String(leftDist) + ",";
    jsonData += "\"right_distance\":" + String(rightDist) + ",";
    jsonData += "\"ir_distance\":" + String(irDistance) + ",";
    jsonData += "\"mode\":" + String(currentMode) + ",";
    jsonData += "\"power_status\":\"" + String(powerOn ? "true" : "false") + "\",";
    jsonData += "\"battery_level\":100,";
    jsonData += "\"wifi_connected\":true,";
    jsonData += "\"wifi_strength\":" + String(WiFi.RSSI());
    jsonData += "}";

    Serial.print("[SERVER] Data: ");
    Serial.println(jsonData);

    // Gửi POST request
    Serial.println("[SERVER] Đang gửi POST request...");
    int httpCode = http.POST(jsonData);

    Serial.print("[SERVER] HTTP Code: ");
    Serial.println(httpCode);

    if (httpCode == HTTP_CODE_OK)
    {
        Serial.println("[SERVER] ✅ POST thành công!");
        String response = http.getString();
        Serial.print("[SERVER] Response: ");
        Serial.println(response);
    }
    else if (httpCode > 0)
    {
        Serial.print("[SERVER] ⚠️ HTTP Code: ");
        Serial.println(httpCode);
        String response = http.getString();
        if (response.length() > 0)
        {
            Serial.print("[SERVER] Response: ");
            Serial.println(response);
        }
    }
    else
    {
        Serial.print("[SERVER] ❌ Lỗi: ");
        Serial.println(http.errorToString(httpCode));
    }

    http.end();
    Serial.println("[SERVER] Đã đóng kết nối\n");
}

// ============================================
// SETUP
// ============================================
void setup()
{
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n════════════════════════════════════════");
    Serial.println("        GẬY THÔNG MINH - ESP32");
    Serial.println("════════════════════════════════════════\n");

    Serial.println("[SYSTEM] 🔄 Khởi động hệ thống...");

    // Khởi tạo OLED
    Serial.println("[OLED] 🔄 Khởi tạo màn hình...");
    Wire.begin(OLED_SDA, OLED_SCL);
    u8g2.begin();
    showWelcomeScreen();

    // Thiết lập pins
    Serial.println("[PINS] 🔄 Thiết lập chân GPIO...");
    setupPins();

    // Kết nối WiFi
    Serial.println("[WIFI] 🔄 Đang kết nối WiFi...");
    scanWiFiNetworks();
    connectToWiFi();

    // Khởi tạo ThingSpeak
    Serial.println("[THINGSPEAK] 🔄 Khởi tạo...");
    ThingSpeak.begin(client);

    Serial.println("\n════════════════════════════════════════");
    Serial.println("[SYSTEM] ✅ Hệ thống đã sẵn sàng!");
    Serial.print("[SERVER] 📡 URL: ");
    Serial.println(SERVER_URL);
    Serial.println("════════════════════════════════════════\n");
}

// ============================================
// PIN SETUP
// ============================================
void setupPins()
{
    // Ultrasonic Sensors
    pinMode(TRIG_F, OUTPUT);
    pinMode(ECHO_F, INPUT);
    pinMode(TRIG_L, OUTPUT);
    pinMode(ECHO_L, INPUT);
    pinMode(TRIG_R, OUTPUT);
    pinMode(ECHO_R, INPUT);

    // IR Sensor
    pinMode(IR_PIN, INPUT);

    // Outputs
    pinMode(BUZZER, OUTPUT);
    pinMode(VIB_PIN, OUTPUT);

    // Buttons
    pinMode(POWER_PIN, INPUT_PULLUP);
    pinMode(MODE_PIN, INPUT_PULLUP);

    // RGB LED
    pinMode(LED_R, OUTPUT);
    pinMode(LED_G, OUTPUT);
    pinMode(LED_B, OUTPUT);

    // Đặt trạng thái ban đầu
    digitalWrite(BUZZER, LOW);
    digitalWrite(VIB_PIN, LOW);
    setRGB(0, 0, 0);
}

// ============================================
// WIFI SCANNER
// ============================================
void scanWiFiNetworks()
{
    Serial.println("[WIFI] 🔍 Quét mạng WiFi...");

    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    delay(100);

    int n = WiFi.scanNetworks();
    if (n == 0)
    {
        Serial.println("[WIFI] ❌ Không tìm thấy mạng WiFi!");
    }
    else
    {
        Serial.print("[WIFI] 📡 Tìm thấy ");
        Serial.print(n);
        Serial.println(" mạng WiFi");
    }

    WiFi.scanDelete();
}

// ============================================
// KẾT NỐI WIFI
// ============================================
void connectToWiFi()
{
    Serial.print("[WIFI] 📶 Kết nối đến: ");
    Serial.println(WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30)
    {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    Serial.println();

    if (WiFi.status() == WL_CONNECTED)
    {
        Serial.println("[WIFI] ✅ Đã kết nối WiFi!");
        Serial.print("[WIFI] 📡 RSSI: ");
        Serial.print(WiFi.RSSI());
        Serial.println(" dBm");
        Serial.print("[WIFI] 🌐 IP: ");
        Serial.println(WiFi.localIP());
        Serial.print("[WIFI] 🚪 Gateway: ");
        Serial.println(WiFi.gatewayIP());
    }
    else
    {
        Serial.println("[WIFI] ❌ Lỗi kết nối WiFi!");
        Serial.print("[WIFI] 📊 Status code: ");
        Serial.println(WiFi.status());
    }
}

// ============================================
// LOOP CHÍNH
// ============================================
void loop()
{
    // Kiểm tra nút nhấn
    checkButtons();

    // Nếu nguồn tắt, hiển thị màn hình sleep
    if (!powerOn)
    {
        showSleepScreen();
        return;
    }

    // Đọc cảm biến
    readSensors();

    // Xử lý chế độ
    if (currentMode == 1)
    {
        processSensorMode();
    }
    else
    {
        processAlertMode();
    }

    // Gửi dữ liệu lên server mỗi 5 giây
    if (millis() - lastServerSend > 5000)
    {
        Serial.println("\n[SERVER] ⏰ Đến lượt gửi dữ liệu...");
        sendToServer();
        lastServerSend = millis();
    }

    // Hiển thị OLED
    displayOLEDWithIcons();

    // Gửi lên ThingSpeak
    uploadToCloud();

    // Debug info mỗi 30 giây
    if (millis() - lastDebugTime > 30000)
    {
        debugInfo();
        lastDebugTime = millis();
    }

    delay(50);
}

// ============================================
// DEBUG INFO
// ============================================
void debugInfo()
{
    Serial.println("\n════════════════════════════════════════");
    Serial.println("[DEBUG] 📊 Thông tin hệ thống:");
    Serial.print("[DEBUG] WiFi Status: ");
    Serial.println(WiFi.status() == WL_CONNECTED ? "Connected" : "Disconnected");
    Serial.print("[DEBUG] Power: ");
    Serial.println(powerOn ? "ON" : "OFF");
    Serial.print("[DEBUG] Mode: ");
    Serial.println(currentMode);
    Serial.print("[DEBUG] Sensors - F: ");
    Serial.print(frontDist);
    Serial.print(" L: ");
    Serial.print(leftDist);
    Serial.print(" R: ");
    Serial.print(rightDist);
    Serial.print(" IR: ");
    Serial.println(irDistance);
    Serial.print("[DEBUG] Next server send: ");
    Serial.println((5000 - (millis() - lastServerSend)) / 1000);
    Serial.println("════════════════════════════════════════\n");
}

// ============================================
// XỬ LÝ NÚT NHẤN
// ============================================
void checkButtons()
{
    static unsigned long lastCheck = 0;
    if (millis() - lastCheck < 50)
        return;
    lastCheck = millis();

    int powerState = digitalRead(POWER_PIN);
    int modeState = digitalRead(MODE_PIN);

    // Nút nguồn
    if (powerState == LOW && lastPowerState == HIGH)
    {
        delay(30); // Debounce
        if (digitalRead(POWER_PIN) == LOW)
        {
            powerOn = !powerOn;
            Serial.print("[BUTTON] 🔘 NGUỒN: ");
            Serial.println(powerOn ? "BẬT" : "TẮT");

            if (powerOn)
            {
                powerOnEffect();
                showBootScreen();
            }
            else
            {
                powerOffEffect();
            }
            delay(300);
        }
    }

    // Nút chế độ
    if (powerOn && modeState == LOW && lastModeState == HIGH)
    {
        delay(30); // Debounce
        if (digitalRead(MODE_PIN) == LOW)
        {
            currentMode = (currentMode == 1) ? 2 : 1;
            Serial.print("[BUTTON] 🔘 CHẾ ĐỘ: M");
            Serial.println(currentMode);

            // Báo hiệu bằng âm thanh
            tone(BUZZER, 1000, 100);
            delay(150);
            tone(BUZZER, 1500, 100);

            showModeScreen();
            delay(300);
        }
    }

    lastPowerState = powerState;
    lastModeState = modeState;
}

// ============================================
// ĐỌC CẢM BIẾN
// ============================================
void readSensors()
{
    frontDist = getDistance(TRIG_F, ECHO_F);
    leftDist = getDistance(TRIG_L, ECHO_L);
    rightDist = getDistance(TRIG_R, ECHO_R);
    irValue = analogRead(IR_PIN);

    // Tính khoảng cách IR
    if (irValue > 100)
    {
        irDistance = 10650.08 * pow(irValue, -0.935) - 10;
        if (irDistance < 10)
            irDistance = 10;
        if (irDistance > 80)
            irDistance = 80;
    }
    else
    {
        irDistance = 80;
    }

    // In giá trị cảm biến
    Serial.print("[SENSOR] 📊 Trước=");
    Serial.print(frontDist);
    Serial.print("cm | Trái=");
    Serial.print(leftDist);
    Serial.print("cm | Phải=");
    Serial.print(rightDist);
    Serial.print("cm | IR=");
    Serial.print(irDistance);
    Serial.println("cm");
}

int getDistance(int trig, int echo)
{
    digitalWrite(trig, LOW);
    delayMicroseconds(2);
    digitalWrite(trig, HIGH);
    delayMicroseconds(10);
    digitalWrite(trig, LOW);

    long t = pulseIn(echo, HIGH, 30000);
    if (t == 0)
        return 999;

    int d = t * 0.034 / 2;
    return (d > 0 && d < 300) ? d : 999;
}

// ============================================
// XỬ LÝ CHẾ ĐỘ CẢM BIẾN
// ============================================
void processSensorMode()
{
    bool alert = false;

    // Kiểm tra phía trước
    if (frontDist <= DANGER_DIST && frontDist > 0)
    {
        setRGB(255, 0, 0); // Đỏ
        digitalWrite(VIB_PIN, HIGH);
        tone(BUZZER, 2000); // Còi liên tục
        alert = true;
        Serial.println("[ALERT] ⚠️ NGUY HIỂM phía trước!");
    }
    else if (frontDist <= WARN_DIST && frontDist > 0)
    {
        setRGB(255, 150, 0); // Cam
        digitalWrite(VIB_PIN, HIGH);
        tone(BUZZER, 1500, 200); // Còi ngắt quãng
        delay(200);
        digitalWrite(VIB_PIN, LOW);
        noTone(BUZZER);
        alert = true;
        Serial.println("[ALERT] ⚠️ Cảnh báo phía trước!");
    }

    // Nếu không có cảnh báo phía trước
    if (!alert)
    {
        if (leftDist <= WARN_DIST && leftDist > 0)
        {
            setRGB(0, 255, 255); // Xanh cyan
            tone(BUZZER, 1100, 150);
            Serial.println("[ALERT] ⚠️ Có vật thể bên trái!");
        }
        if (rightDist <= WARN_DIST && rightDist > 0)
        {
            setRGB(255, 100, 200); // Hồng
            tone(BUZZER, 1300, 150);
            Serial.println("[ALERT] ⚠️ Có vật thể bên phải!");
        }
    }

    // Kiểm tra cảm biến IR
    if (irDistance < IR_GROUND)
    {
        setRGB(100, 100, 100); // Xám
        Serial.println("[ALERT] ⚠️ Mặt đất không bằng phẳng!");
    }

    // Nếu không có cảnh báo nào
    if (!alert)
    {
        setRGB(0, 255, 0); // Xanh lá
        digitalWrite(VIB_PIN, LOW);
        noTone(BUZZER);
    }
}

// ============================================
// XỬ LÝ CHẾ ĐỘ CẢNH BÁO
// ============================================
void processAlertMode()
{
    bool alert = false;

    if (frontDist <= DANGER_DIST && frontDist > 0)
    {
        setRGB(255, 0, 0);
        digitalWrite(VIB_PIN, HIGH);
        tone(BUZZER, 2000);
        alert = true;
        Serial.println("[ALERT] ⚠️ NGUY HIỂM phía trước!");
    }
    else if (frontDist <= WARN_DIST && frontDist > 0)
    {
        setRGB(255, 100, 0);
        for (int i = 0; i < 2; i++)
        {
            digitalWrite(VIB_PIN, HIGH);
            tone(BUZZER, 1500, 100);
            delay(100);
            digitalWrite(VIB_PIN, LOW);
            noTone(BUZZER);
            delay(50);
        }
        alert = true;
        Serial.println("[ALERT] ⚠️ Cảnh báo phía trước!");
    }

    if (leftDist <= WARN_DIST && leftDist > 0)
    {
        for (int i = 0; i < 1; i++)
        {
            digitalWrite(VIB_PIN, HIGH);
            delay(100);
            digitalWrite(VIB_PIN, LOW);
            delay(50);
        }
        alert = true;
        Serial.println("[ALERT] ⚠️ Có vật thể bên trái!");
    }
    if (rightDist <= WARN_DIST && rightDist > 0)
    {
        for (int i = 0; i < 2; i++)
        {
            digitalWrite(VIB_PIN, HIGH);
            delay(50);
            digitalWrite(VIB_PIN, LOW);
            delay(30);
        }
        alert = true;
        Serial.println("[ALERT] ⚠️ Có vật thể bên phải!");
    }

    if (irDistance < IR_GROUND)
    {
        setRGB(100, 100, 100);
        Serial.println("[ALERT] ⚠️ Mặt đất không bằng phẳng!");
    }

    if (!alert)
    {
        setRGB(0, 255, 0);
        digitalWrite(VIB_PIN, LOW);
        noTone(BUZZER);
    }
}

// ============================================
// HIỂN THỊ MÀN HÌNH
// ============================================
void showWelcomeScreen()
{
    u8g2.clearBuffer();
    u8g2.setFont(u8g2_font_7x13_tr);
    u8g2.drawStr(15, 20, "GAY THONG MINH");

    u8g2.drawXBM(40, 35, 8, 8, icon_up);
    u8g2.drawXBM(55, 35, 8, 8, icon_left);
    u8g2.drawXBM(70, 35, 8, 8, icon_right);
    u8g2.drawXBM(85, 35, 8, 8, icon_down);

    u8g2.setFont(u8g2_font_5x8_tr);
    u8g2.drawStr(25, 55, "Nhan NUT NGUON");
    u8g2.sendBuffer();
    delay(2000);
}

void showSleepScreen()
{
    u8g2.clearBuffer();
    u8g2.setFont(u8g2_font_7x13_tr);
    u8g2.drawStr(30, 30, "TAT NGUON");

    u8g2.drawXBM(50, 45, 8, 8, icon_error);

    u8g2.setFont(u8g2_font_5x8_tr);
    u8g2.drawStr(30, 60, "Nhan de BAT");
    u8g2.sendBuffer();
    delay(100);
}

void showBootScreen()
{
    u8g2.clearBuffer();
    u8g2.setFont(u8g2_font_7x13_tr);
    u8g2.drawStr(40, 30, "BAT NGUON");

    u8g2.drawXBM(50, 45, 8, 8, icon_ok);

    u8g2.setFont(u8g2_font_5x8_tr);
    u8g2.drawStr(20, 60, "He thong san sang");
    u8g2.sendBuffer();
    delay(1000);
}

void showModeScreen()
{
    u8g2.clearBuffer();
    u8g2.setFont(u8g2_font_7x13_tr);
    u8g2.drawStr(25, 30, "DOI CHE DO");

    u8g2.drawXBM(50, 45, 8, 8, currentMode == 1 ? icon_up : icon_warning);

    u8g2.setFont(u8g2_font_6x10_tr);
    u8g2.setCursor(40, 60);
    u8g2.print("MODE ");
    u8g2.print(currentMode);
    u8g2.sendBuffer();
    delay(800);
}

void displayOLEDWithIcons()
{
    u8g2.clearBuffer();
    u8g2.setFont(u8g2_font_6x10_tr);

    // Dòng 1: Trạng thái nguồn
    u8g2.setCursor(0, 10);
    if (powerOn)
    {
        u8g2.drawXBM(0, 2, 8, 8, icon_ok);
        u8g2.setCursor(10, 10);
        u8g2.print("ON");
    }
    else
    {
        u8g2.drawXBM(0, 2, 8, 8, icon_error);
        u8g2.setCursor(10, 10);
        u8g2.print("OFF");
    }

    // Dòng 1: Chế độ
    u8g2.setCursor(40, 10);
    u8g2.print("M");
    u8g2.print(currentMode);
    u8g2.print(":");
    u8g2.print(currentMode == 1 ? "SEN" : "ALT");

    // Dòng 2: Cảm biến phía trước
    u8g2.drawXBM(0, 20, 8, 8, icon_up);
    u8g2.setCursor(10, 28);
    u8g2.print(":");
    if (frontDist == 999)
    {
        u8g2.print("---");
    }
    else
    {
        u8g2.print(frontDist);
        u8g2.print("cm");
    }

    // Cảnh báo phía trước
    if (frontDist <= DANGER_DIST && frontDist > 0)
    {
        u8g2.drawXBM(90, 20, 8, 8, icon_error);
        u8g2.setCursor(100, 28);
        u8g2.print("STOP");
    }
    else if (frontDist <= WARN_DIST && frontDist > 0)
    {
        u8g2.drawXBM(90, 20, 8, 8, icon_warning);
        u8g2.setCursor(100, 28);
        u8g2.print("WARN");
    }

    // Dòng 3: Cảm biến trái/phải
    u8g2.drawXBM(0, 38, 8, 8, icon_left);
    u8g2.setCursor(10, 46);
    if (leftDist == 999)
    {
        u8g2.print("---");
    }
    else
    {
        u8g2.print(leftDist);
    }

    u8g2.drawXBM(40, 38, 8, 8, icon_right);
    u8g2.setCursor(50, 46);
    if (rightDist == 999)
    {
        u8g2.print("---");
    }
    else
    {
        u8g2.print(rightDist);
    }

    // Dòng 3: Cảm biến IR
    u8g2.setCursor(80, 46);
    if (irDistance < IR_GROUND)
    {
        u8g2.drawXBM(80, 38, 8, 8, icon_ground);
        u8g2.setCursor(90, 46);
        u8g2.print("GRND");
    }
    else if (irDistance > IR_HOLE)
    {
        u8g2.drawXBM(80, 38, 8, 8, icon_hole);
        u8g2.setCursor(90, 46);
        u8g2.print("HOLE!");
    }

    // Dòng 4: Thông tin IR và màu LED
    u8g2.setCursor(0, 56);
    u8g2.print("IR:");
    if (irDistance >= 80)
    {
        u8g2.print("---");
    }
    else
    {
        u8g2.print(irDistance);
        u8g2.print("cm");
    }

    u8g2.setCursor(70, 56);
    if (frontDist <= DANGER_DIST && frontDist > 0)
    {
        u8g2.print("RED");
    }
    else if (frontDist <= WARN_DIST && frontDist > 0)
    {
        u8g2.print("ORN");
    }
    else if (irDistance < IR_GROUND)
    {
        u8g2.print("GRY");
    }
    else
    {
        u8g2.print("GRN");
    }

    u8g2.sendBuffer();
}

// ============================================
// HÀM PHỤ TRỢ
// ============================================
void setRGB(int r, int g, int b)
{
    analogWrite(LED_R, 255 - constrain(r, 0, 255));
    analogWrite(LED_G, 255 - constrain(g, 0, 255));
    analogWrite(LED_B, 255 - constrain(b, 0, 255));
}

void powerOnEffect()
{
    Serial.println("[EFFECT] 💡 Hiệu ứng bật nguồn...");
    for (int i = 0; i < 3; i++)
    {
        setRGB(0, 255, 0); // Xanh lá
        delay(200);
        setRGB(0, 0, 0); // Tắt
        delay(200);
    }
    tone(BUZZER, 1500, 200);
    delay(300);
    digitalWrite(VIB_PIN, LOW);
    tone(BUZZER, 2000, 200);
    delay(500);
}

void powerOffEffect()
{
    Serial.println("[EFFECT] 💡 Hiệu ứng tắt nguồn...");
    setRGB(255, 0, 0); // Đỏ
    delay(200);
    setRGB(0, 0, 255); // Xanh dương
    delay(200);
    setRGB(0, 0, 0); // Tắt
    digitalWrite(VIB_PIN, LOW);
    tone(BUZZER, 1000, 300);
    delay(500);
}

// ============================================
// UPLOAD TO THINGSPEAK
// ============================================
void uploadToCloud()
{
    if (WiFi.status() != WL_CONNECTED)
    {
        return;
    }

    if (millis() - lastSendTime > SEND_INTERVAL)
    {
        Serial.println("[THINGSPEAK] ☁️ Đang gửi dữ liệu...");

        ThingSpeak.setField(1, frontDist);
        ThingSpeak.setField(2, leftDist);
        ThingSpeak.setField(3, rightDist);
        ThingSpeak.setField(4, irDistance);
        ThingSpeak.setField(5, currentMode);

        int httpCode = ThingSpeak.writeFields(THINGSPEAK_CHANNEL, THINGSPEAK_API_KEY);

        if (httpCode == 200)
        {
            Serial.println("[THINGSPEAK] ✅ Đã gửi thành công!");
        }
        else
        {
            Serial.print("[THINGSPEAK] ❌ Lỗi: ");
            Serial.println(httpCode);
        }

        lastSendTime = millis();
    }
}