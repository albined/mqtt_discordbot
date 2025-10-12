# Discord MQTT Bot

A Discord bot that relays messages from MQTT to Discord users and channels using modern slash commands. Perfect for home automation notifications, IoT alerts, and more!

## Features

- 🔔 Relay MQTT messages to Discord users (DMs) or channels
- ⚡ Modern Discord slash commands (/)
- 👤 User registration with custom names
- 📢 Channel registration with custom names
- 💾 Persistent storage (survives bot restarts)
- 🐳 Docker support for easy deployment
- 🔒 Secure credential management via environment variables

## Setup

### Prerequisites

- Python 3.11+ (for local development)
- Docker and Docker Compose (for containerized deployment)
- A Discord Bot Token (see [DISCORD_SETUP.md](DISCORD_SETUP.md) for detailed instructions)
- MQTT broker access (e.g., Mosquitto)

### Configuration

1. **Set up your Discord bot:** Follow the detailed guide in [DISCORD_SETUP.md](DISCORD_SETUP.md)

2. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

3. Edit `.env` and fill in your credentials:
```env
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_APPLICATION_ID=your_application_id_here
DISCORD_PUBLIC_KEY=your_public_key_here

MQTT_BROKER=mqtt://your_mosquitto_url:1883
MQTT_USERNAME=your_mqtt_username
MQTT_PASSWORD=your_mqtt_password
MQTT_TOPIC=/home/discord-bot/messages
```

### Running Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the bot:
```bash
python bot.py
```

### Running with Docker

1. Build and start the container:
```bash
docker-compose up -d
```

2. View logs:
```bash
docker-compose logs -f
```

3. Stop the container:
```bash
docker-compose down
```

## Usage

### Discord Slash Commands

All commands use Discord's modern slash command system. Just type `/` in Discord to see available commands!

- `/me <name>` - Register yourself with a name for receiving notifications
- `/channel <name>` - Register the current channel with a name
- `/unregister` - Unregister yourself or the current channel
- `/list` - List all registered names
- `/example` - Show MQTT payload example
- `/help` - Show help message

**Note:** Slash commands may take up to 1 hour to appear after first starting the bot (global sync). See [DISCORD_SETUP.md](DISCORD_SETUP.md) for instant testing options.

### MQTT Message Format

Send messages to the configured MQTT topic with the following JSON payload:

```json
{
  "target_id": "your_registered_name",
  "message": "The front door has been opened.",
  "source": "Front Door Sensor"
}
```

**Fields:**
- `target_id` (required) - The registered name (user or channel)
- `message` (required) - The message content to send
- `source` (optional) - Where the message is coming from (defaults to "Unknown")

### Example with mosquitto_pub

```bash
mosquitto_pub -h your_broker -u username -P password \
  -t "/home/discord-bot/messages" \
  -m '{"target_id": "john", "message": "Hello from MQTT!", "source": "Test System"}'
```

## How It Works

1. Users or channels register themselves with a unique name using `!me <name>` or `!channel <name>`
2. External services (home automation, IoT devices, etc.) publish MQTT messages to the configured topic
3. The bot receives the MQTT message and looks up the registered name
4. The bot sends the message to the corresponding Discord user (DM) or channel
5. All registrations are stored in `data/registry.json` and persist through restarts

## Important Notes

- Names are shared between users and channels (no duplicates allowed)
- Each user/channel can only have one registered name at a time
- To change your name, first use `!unregister`, then register with a new name
- The bot needs proper Discord permissions to send DMs and messages to channels
- Make sure to mount the `data` directory when using Docker to persist registrations

## Discord Bot Permissions

When inviting your bot to a server, make sure it has these permissions:
- Read Messages/View Channels
- Send Messages
- Embed Links
- Read Message History

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

## License

MIT License - Feel free to use and modify as needed!
