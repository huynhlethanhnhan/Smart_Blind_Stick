#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>
#include <U8g2lib.h>

// ============================================
// OLED CONFIGURATION
// ============================================
extern U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2;

// ============================================
// PIN DEFINITIONS
// ============================================
#define OLED_SDA 21
#define OLED_SCL 22
#define TRIG_F 13
#define ECHO_F 12
#define TRIG_L 14
#define ECHO_L 27
#define TRIG_R 26
#define ECHO_R 25
#define IR_PIN 34
#define BUZZER 33
#define POWER_PIN 15
#define MODE_PIN 32
#define VIB_PIN 4
#define LED_R 16
#define LED_G 17
#define LED_B 5

// ============================================
// WIFI & THINGSPEAK CONFIGURATION
// ============================================
extern const char *ssid;
extern const char *password;
extern unsigned long myChannelNumber;
extern const char *myWriteAPIKey;

// ============================================
// SYSTEM CONSTANTS
// ============================================
extern const int DANGER_DIST;
extern const int WARN_DIST;
extern const int SAFE_DIST;
extern const int IR_GROUND;
extern const int IR_HOLE;
extern const long sendInterval;

// ============================================
// GLOBAL VARIABLES (Shared across files)
// ============================================
extern bool powerOn;
extern int currentMode;
extern bool lastPowerState;
extern bool lastModeState;
extern unsigned long lastSendTime;

extern int frontDist, leftDist, rightDist;
extern int irValue;
extern int irDistance;

extern WiFiClient client;

// ============================================
// ICON BITMAPS
// ============================================
extern const unsigned char icon_up[];
extern const unsigned char icon_down[];
extern const unsigned char icon_left[];
extern const unsigned char icon_right[];
extern const unsigned char icon_warning[];
extern const unsigned char icon_error[];
extern const unsigned char icon_ok[];
extern const unsigned char icon_ground[];
extern const unsigned char icon_hole[];

#endif