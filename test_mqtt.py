#!/usr/bin/env python3
"""
Test script to send MQTT messages to the Discord bot
Usage: python test_mqtt.py <target_name> <message> [source]
"""

import sys
import json
import paho.mqtt.publish as publish
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

MQTT_BROKER = os.getenv('MQTT_BROKER', 'mqtt://mosquitto.home:1883')
MQTT_USERNAME = os.getenv('MQTT_USERNAME', 'albin')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', 'albinalbinalbin')
MQTT_TOPIC = os.getenv('MQTT_TOPIC', '/home/discord-bot/messages')


def send_message(target_id, message, source="Test Script"):
    """Send a test message via MQTT"""
    
    # Parse broker URL
    broker_url = MQTT_BROKER.replace('mqtt://', '').replace('mqtts://', '')
    host = broker_url.split(':')[0]
    port = int(broker_url.split(':')[1]) if ':' in broker_url else 1883
    
    # Prepare payload
    payload = {
        "target_id": target_id,
        "message": message,
        "source": source
    }
    
    # Auth dict
    auth = None
    if MQTT_USERNAME and MQTT_PASSWORD:
        auth = {
            "username": MQTT_USERNAME,
            "password": MQTT_PASSWORD
        }
    
    try:
        print(f"📤 Sending message to {target_id}...")
        print(f"   Topic: {MQTT_TOPIC}")
        print(f"   Broker: {host}:{port}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        publish.single(
            MQTT_TOPIC,
            payload=json.dumps(payload),
            hostname=host,
            port=port,
            auth=auth
        )
        
        print("✅ Message sent successfully!")
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 3:
        print("Usage: python test_mqtt.py <target_name> <message> [source]")
        print("\nExample:")
        print('  python test_mqtt.py john "Hello from test script!"')
        print('  python test_mqtt.py my_channel "Test notification" "Test System"')
        sys.exit(1)
    
    target_id = sys.argv[1]
    message = sys.argv[2]
    source = sys.argv[3] if len(sys.argv) > 3 else "Test Script"
    
    send_message(target_id, message, source)


if __name__ == "__main__":
    main()
