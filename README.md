# Warning, This project was vibecoded 

## Discord MQTT Bot

A Discord bot that relays messages from MQTT to Discord users and channels using modern slash commands. Perfect for home automation notifications, IoT alerts, and more!

## Features

- 🔔 Relay MQTT messages to Discord users (DMs) or channels
- ⚡ Modern Discord slash commands (/)
- 👤 Smart registration - one command for users and channels
- 💾 Persistent storage (survives bot restarts)
- 🐳 Docker support with optimized multi-stage build
- 🔒 Secure credential management via environment variables

---

## Quick Start

### 1. Configuration

Copy `.env.example` to `.env` and add your credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```env
DISCORD_TOKEN=your_discord_bot_token_here
MQTT_BROKER=mqtt://your_mosquitto_url:1883
MQTT_USERNAME=your_mqtt_username
MQTT_PASSWORD=your_mqtt_password
MQTT_TOPIC=/home/discord-bot/messages
```

### 2. Run with Docker (Recommended)

```bash
docker-compose up -d          # Start bot
docker-compose logs -f        # View logs
docker-compose down           # Stop bot
docker-compose up -d --build  # Rebuild after changes
```

### 3. Run Locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

---

## Discord Commands

| Command | Where to Use | Description |
|---------|--------------|-------------|
| `/register <name>` | DM or Channel | Register yourself (DM) or channel (server) |
| `/unregister` | DM or Channel | Remove your or channel's registration |
| `/list` | Anywhere | Show all registered users and channels |
| `/example` | Anywhere | Show MQTT payload example |
| `/help` | Anywhere | Show help message |

**Pro Tip:** Use `/register` in a DM to register yourself, or in a server channel to register that channel!

---

## MQTT Integration

### Message Format

**Topic:** Set in `.env` (default: `/home/discord-bot/messages`)

**Payload (JSON):**
```json
{
  "target_id": "registered_name",
  "message": "Your message here",
  "source": "Source Name"
}
```

### Testing

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

**Fields:**

- `target_id` (required) - The registered name (user or channel)
- `message` (required) - The message content to send
- `source` (optional) - Where the message is coming from (defaults to "Unknown")

---

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

---

## How It Works

1. Users or channels register with a unique name using `/register <name>`
2. External services (home automation, IoT devices, etc.) publish MQTT messages to the configured topic
3. The bot receives the MQTT message and looks up the registered name
4. The bot sends the message to the corresponding Discord user (DM) or channel
5. All registrations are stored in `data/registry.json` and persist through restarts

---

## Discord Bot Setup

When inviting your bot to a server, ensure it has these permissions:

- Read Messages/View Channels
- Send Messages
- Embed Links
- Read Message History

---

## Troubleshooting

### Bot not receiving MQTT messages

- Check that your MQTT broker URL, username, and password are correct
- Verify the MQTT topic matches what your services are publishing to
- Check the bot logs for connection errors

### Messages not being delivered

- Ensure the target name is registered with `/list`
- Verify the bot has permission to send DMs or messages in the channel
- Check that the Discord ID in the registry is correct

### Docker container won't start

- Verify all environment variables are set in `.env`
- Check the logs with `docker-compose logs`
- Ensure the `data` directory has proper permissions

---

## Data Persistence

- Registrations stored in `data/registry.json`
- With Docker, mount `./data:/app/data` (already configured)
- Data persists through container restarts
- Backup: `cp data/registry.json data/registry.json.backup`

---

## Security Notes

- Never commit `.env` file to git (already in `.gitignore`)
- Use strong passwords for MQTT
- Consider using MQTT over TLS (mqtts://)
- Limit bot permissions to minimum required
- Regular backup of `data/registry.json`

---

## File Structure

```plaintext
discord_notif/
├── .env.example          # Environment template
├── Dockerfile           # Optimized multi-stage build
├── docker-compose.yml   # Docker compose config
├── README.md            # This file
├── bot.py               # Main bot code
├── requirements.txt     # Python dependencies
├── test_mqtt.py         # MQTT test script
└── data/                # Persistent storage (auto-created)
    └── registry.json    # User/channel registrations
```

---

## License

MIT License - Feel free to use and modify as needed!
