/*
Simple Ethernet wrapper for the IBIS protocol.
(C) 2015 Julian Metzler
*/

#include <SPI.h>
#include <Ethernet.h>

#define REFRESH_TIMEOUT 120000 // Two minutes

byte ETH_MAC[] = {0xC0, 0xFF, 0xEE, 0xC0, 0xFF, 0xEE};
short ETH_PORT = 1337;

EthernetServer ibisServer(ETH_PORT);
char currentText[150];
int lastRefresh = millis();

void sendIBIS003c(char* text) {
  strcpy(currentText, text);
  char datagram[150], datagramFormat[10];
  short length = strlen(text);
  short blocks = length / 4;
  short remainder = length % 4;
  
  if(remainder) {
    blocks += 1;
  }
  
  sprintf(datagramFormat, "zI%i%%-%is\r", blocks, blocks * 4);
  sprintf(datagram, datagramFormat, text);
  short datagramLength = strlen(datagram);
  
  short hashByte = 0x7F;
  for(short charPos = 0; charPos < datagramLength; charPos++) {
    short curByte = datagram[charPos];
    hashByte ^= curByte;
  }
  
  Serial.print(datagram);
  Serial.write(hashByte);
  lastRefresh = millis();
}

void preventTimeout() {
  if(millis() - lastRefresh >= REFRESH_TIMEOUT) {
    sendIBIS003c(currentText);
  }
}

void setup() {
  Serial.begin(1200, SERIAL_7E2);
  sendIBIS003c("Obtaining IP...");
  
  if(Ethernet.begin(ETH_MAC) == 0) {
    sendIBIS003c("DHCP failed");
    for(;;);
  }
  
  IPAddress currentIP = Ethernet.localIP();
  char ipText[20];
  sprintf(ipText, "%i.%i.%i.%i:%i", currentIP[0], currentIP[1], currentIP[2], currentIP[3], ETH_PORT);
  sendIBIS003c(ipText);
}

void loop() {
  // Wait for connection
  EthernetClient client = ibisServer.available();
  if(client) {
    char message[150] = {0};
    short messagePos = 0;
    while(client.connected()) {
      if(client.available() > 0) {
        // Read data
        char thisChar = client.read();
        message[messagePos] = thisChar;
        messagePos++;
      }
    }
    
    // Send the message to the display
    sendIBIS003c(message);
  } else {
    preventTimeout();
  }
}
