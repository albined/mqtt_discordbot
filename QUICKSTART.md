# Quick Reference Guide

## Initial Setup

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   - Get Discord token from: https://discord.com/developers/applications
   - Set your MQTT broker details

## Running the Bot

### Option 1: Docker (Recommended)
```bash
./start.sh docker
# or
docker-compose up -d
```

### Option 2: Local Python
```bash
./start.sh
# or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## Discord Commands Cheat Sheet

| Command | Description | Example |
|---------|-------------|---------|
| `/me <name>` | Register yourself | `/me john` |
| `/channel <name>` | Register channel | `/channel alerts` |
| `/unregister` | Remove registration | `/unregister` |
| `/list` | Show all registered names | `/list` |
| `/example` | Show MQTT example | `/example` |
| `/help` | Show help | `/help` |

## MQTT Message Format

**Topic:** (Set in `.env`, default: `/home/discord-bot/messages`)

**Payload:**
```json
{
  "target_id": "registered_name",
  "message": "Your message here",
  "source": "Source Name"
}
```

## Testing MQTT Integration

Use the included test script:
```bash
python test_mqtt.py john "Test message" "Test System"
```

Or use mosquitto_pub:
```bash
mosquitto_pub -h broker.example.com -u username -P password \
  -t "/home/discord-bot/messages" \
  -m '{"target_id":"john","message":"Hello!","source":"Test"}'
```

## File Structure

```
discord_notif/
├── .env.example          # Environment template
├── .gitignore           # Git ignore rules
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Docker compose config
├── README.md            # Full documentation
├── QUICKSTART.md        # This file
├── bot.py               # Main bot code
├── requirements.txt     # Python dependencies
├── start.sh             # Quick start script
├── test_mqtt.py         # MQTT test script
└── data/                # Persistent storage (auto-created)
    └── registry.json    # User/channel registrations
```

## Common Issues

### Bot not receiving MQTT messages
- ✅ Check MQTT broker URL in `.env`
- ✅ Verify credentials
- ✅ Ensure topic matches

### Messages not delivered
- ✅ Check target is registered with `/list`
- ✅ Verify bot has permission to DM/message
- ✅ Check bot logs

### Docker issues
- ✅ Ensure `.env` file exists
- ✅ Check logs: `docker-compose logs -f`
- ✅ Verify data directory permissions

## Docker Commands

```bash
# Start bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop bot
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Restart bot
docker-compose restart
```

## Data Persistence

- Registrations stored in `data/registry.json`
- With Docker, mount `./data:/app/data` (already configured)
- Data persists through container restarts
- Backup: `cp data/registry.json data/registry.json.backup`

## Integration Examples

### Home Assistant
```yaml
automation:
  - alias: "Door Notification"
    trigger:
      platform: state
      entity_id: binary_sensor.front_door
      to: 'on'
    action:
      service: mqtt.publish
      data:
        topic: "/home/discord-bot/messages"
        payload: '{"target_id":"john","message":"Front door opened!","source":"Home Assistant"}'
```

### Node-RED
Use MQTT out node with JSON payload:
```javascript
msg.payload = {
    target_id: "john",
    message: "Temperature alert: 25°C",
    source: "Node-RED"
};
return msg;
```

### Python Script
```python
import paho.mqtt.publish as publish
import json

payload = {
    "target_id": "alerts_channel",
    "message": "System backup completed",
    "source": "Backup Script"
}

publish.single(
    "/home/discord-bot/messages",
    payload=json.dumps(payload),
    hostname="broker.example.com",
    auth={"username": "user", "password": "pass"}
)
```

## Security Notes

- Never commit `.env` file to git (already in `.gitignore`)
- Use strong passwords for MQTT
- Consider using MQTT over TLS (mqtts://)
- Limit bot permissions to minimum required
- Regular backup of `data/registry.json`
