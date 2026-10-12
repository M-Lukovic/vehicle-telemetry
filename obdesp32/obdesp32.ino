#include "BluetoothSerial.h"

BluetoothSerial obd;

const char* adapterPin = "1234";
uint8_t adapterAddress[] = {0x66, 0x1E, 0x32, 0x30, 0x5C, 0x65};

// Send a command and wait for the adapter's response prompt.
String readResponse(const char* command,
                    unsigned long timeoutMs) {
  while (obd.available()) {
    obd.read();
  }

  obd.print(command);
  obd.print('\r');

  String response;
  unsigned long startTime = millis();

  while (millis() - startTime < timeoutMs) {
    while (obd.available()) {
      char character = obd.read();

      if (character == '>') {
        return response;
      }

      response += character;
    }

    delay(5);
  }

  // Do not use an incomplete response as a measurement.
  return "";
}

bool connectAdapter() {
  Serial.println("# Connecting to the OBD adapter...");

  if (!obd.connect(adapterAddress)) {
    Serial.println("# Connection failed.");
    return false;
  }

  Serial.println("# Bluetooth connected.");

  readResponse("ATZ", 5000);   // Reset the adapter.
  readResponse("ATE0", 2000);  // Disable command echo.
  readResponse("ATH0", 2000);  // Disable response headers.
  readResponse("ATS1", 2000);  // Enable spaces between bytes.
  readResponse("ATSP0", 2000); // Select the vehicle protocol automatically.

  Serial.println("uptime_ms,rpm");
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  obd.begin("ESP32-OBD", true);
  obd.setPin(adapterPin);

  connectAdapter();
}

void loop() {
  if (!obd.connected()) {
    delay(3000);
    connectAdapter();
    return;
  }

  // Request engine speed.
  String response = readResponse("010C", 10000);
  response.toUpperCase();

  int position = response.indexOf("41 0C");

  if (position >= 0) {
    unsigned int byteA, byteB;

    if (sscanf(response.c_str() + position,
               "41 0C %x %x", &byteA, &byteB) == 2 &&
        byteA <= 255 && byteB <= 255) {
      // Convert the response bytes to revolutions per minute.
      float rpm = (byteA * 256 + byteB) / 4.0;

      Serial.print(millis());
      Serial.print(',');
      Serial.println(rpm, 2);
    } else {
      Serial.println("# Invalid engine speed response.");
    }
  } else {
    Serial.println("# No valid engine speed reading.");
  }

  delay(1000);
}