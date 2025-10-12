#!/usr/bin/env python3
"""
Discord Bot with MQTT Message Relay
Allows users and channels to register names and receive MQTT messages
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional
import discord
from discord import app_commands
from discord.ext import commands
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mqtt://localhost:1883')
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_TOPIC = os.getenv('MQTT_TOPIC', '/home/discord-bot/messages')
DATA_PATH = Path(os.getenv('DATA_PATH', './data'))

# Ensure data directory exists
DATA_PATH.mkdir(parents=True, exist_ok=True)
REGISTRY_FILE = DATA_PATH / 'registry.json'


class Registry:
    """Manages user and channel name registrations"""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.data: Dict[str, str] = {}
        self.load()
    
    def load(self):
        """Load registry from file"""
        if self.filepath.exists():
            try:
                with open(self.filepath, 'r') as f:
                    self.data = json.load(f)
                logger.info(f"Loaded {len(self.data)} registered names")
            except Exception as e:
                logger.error(f"Error loading registry: {e}")
                self.data = {}
        else:
            self.data = {}
            self.save()
    
    def save(self):
        """Save registry to file"""
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.data, f, indent=2)
            logger.info("Registry saved")
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
    
    def register(self, name: str, discord_id: str) -> bool:
        """Register a name to a Discord ID. Returns True if successful."""
        if name in self.data:
            return False
        self.data[name] = discord_id
        self.save()
        return True
    
    def unregister(self, name: str) -> bool:
        """Unregister a name. Returns True if successful."""
        if name in self.data:
            del self.data[name]
            self.save()
            return True
        return False
    
    def get_id(self, name: str) -> Optional[str]:
        """Get Discord ID for a name"""
        return self.data.get(name)
    
    def get_name(self, discord_id: str) -> Optional[str]:
        """Get name for a Discord ID"""
        for name, id_val in self.data.items():
            if id_val == discord_id:
                return name
        return None
    
    def list_all(self) -> Dict[str, str]:
        """Get all registrations"""
        return self.data.copy()


class MQTTHandler:
    """Handles MQTT connection and message processing"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        # Set username and password if provided
        if MQTT_USERNAME and MQTT_PASSWORD:
            self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    def on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback when connected to MQTT broker"""
        if reason_code == 0:
            logger.info(f"Connected to MQTT broker, subscribing to {MQTT_TOPIC}")
            client.subscribe(MQTT_TOPIC)
        else:
            logger.error(f"Failed to connect to MQTT broker: {reason_code}")
    
    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        """Callback when disconnected from MQTT broker"""
        logger.warning(f"Disconnected from MQTT broker: {reason_code}")
    
    def on_message(self, client, userdata, msg):
        """Callback when MQTT message is received"""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received MQTT message: {payload}")
            
            # Schedule the Discord message sending
            asyncio.run_coroutine_threadsafe(
                self.send_discord_message(payload),
                self.bot.loop
            )
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    async def send_discord_message(self, payload: dict):
        """Send message to Discord based on payload"""
        try:
            target_name = payload.get('target_id')
            message = payload.get('message')
            source = payload.get('source', 'Unknown')
            
            if not target_name or not message:
                logger.error("Invalid payload: missing target_id or message")
                return
            
            # Get Discord ID from registry
            discord_id = self.bot.registry.get_id(target_name)
            if not discord_id:
                logger.error(f"Target '{target_name}' not found in registry")
                return
            
            # Format the message
            formatted_message = f"**{source}**\n{message}"
            
            # Try to send as DM to user
            try:
                user = await self.bot.fetch_user(int(discord_id))
                await user.send(formatted_message)
                logger.info(f"Sent DM to user {target_name} ({discord_id})")
                return
            except (discord.NotFound, discord.HTTPException, ValueError):
                pass
            
            # Try to send to channel
            try:
                channel = await self.bot.fetch_channel(int(discord_id))
                await channel.send(formatted_message)
                logger.info(f"Sent message to channel {target_name} ({discord_id})")
                return
            except (discord.NotFound, discord.HTTPException, ValueError):
                pass
            
            logger.error(f"Could not send message to {target_name} ({discord_id})")
            
        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            # Parse MQTT broker URL
            broker_url = MQTT_BROKER.replace('mqtt://', '').replace('mqtts://', '')
            host = broker_url.split(':')[0]
            port = int(broker_url.split(':')[1]) if ':' in broker_url else 1883
            
            logger.info(f"Connecting to MQTT broker at {host}:{port}")
            self.client.connect(host, port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()


class DiscordBot(commands.Bot):
    """Discord bot with MQTT integration"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(command_prefix='/', intents=intents)
        
        self.registry = Registry(REGISTRY_FILE)
        self.mqtt_handler = None
    
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Bot is starting up...")
        
        # Initialize MQTT handler
        self.mqtt_handler = MQTTHandler(self)
        self.mqtt_handler.connect()
        
        # Sync slash commands
        logger.info("Syncing slash commands...")
        await self.tree.sync()
        logger.info("Slash commands synced!")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'Bot logged in as {self.user.name} ({self.user.id})')
        logger.info(f'Listening to MQTT topic: {MQTT_TOPIC}')
    
    async def close(self):
        """Called when the bot is shutting down"""
        logger.info("Bot is shutting down...")
        if self.mqtt_handler:
            self.mqtt_handler.disconnect()
        await super().close()


# Create bot instance
bot = DiscordBot()



@bot.tree.command(name="register", description="Register yourself (in DM) or channel with a name for notifications")
@app_commands.describe(name="The name you want to register with")
async def register(interaction: discord.Interaction, name: str):
    """Register yourself or channel with a name for receiving notifications"""
    # Check if command is used in DM or in a channel
    is_dm = isinstance(interaction.channel, discord.DMChannel)
    
    if is_dm:
        # Register user
        target_id = str(interaction.user.id)
        target_type = "user"
        target_display = interaction.user.name
    else:
        # Register channel
        target_id = str(interaction.channel_id)
        target_type = "channel"
        target_display = interaction.channel.name
    
    # Check if already registered
    existing_name = bot.registry.get_name(target_id)
    if existing_name:
        await interaction.response.send_message(
            f"❌ This {target_type} is already registered as `{existing_name}`. Unregister first with `/unregister`",
            ephemeral=True
        )
        return
    
    # Try to register
    if bot.registry.register(name, target_id):
        if is_dm:
            await interaction.response.send_message(f"✅ Successfully registered you as `{name}`")
            logger.info(f"User {interaction.user.name} ({target_id}) registered as {name}")
        else:
            await interaction.response.send_message(f"✅ Successfully registered this channel as `{name}`")
            logger.info(f"Channel {target_display} ({target_id}) registered as {name}")
    else:
        await interaction.response.send_message(
            f"❌ Name `{name}` is already taken. Please choose a different name.",
            ephemeral=True
        )


@bot.tree.command(name="unregister", description="Unregister yourself or this channel")
async def unregister(interaction: discord.Interaction):
    """Unregister yourself or this channel"""
    # Check if it's a user or channel unregistering
    user_id = str(interaction.user.id)
    channel_id = str(interaction.channel_id)
    
    user_name = bot.registry.get_name(user_id)
    channel_name = bot.registry.get_name(channel_id)
    
    if user_name:
        bot.registry.unregister(user_name)
        await interaction.response.send_message(f"✅ Successfully unregistered `{user_name}`")
        logger.info(f"User {interaction.user.name} ({user_id}) unregistered from {user_name}")
    elif channel_name:
        bot.registry.unregister(channel_name)
        await interaction.response.send_message(f"✅ Successfully unregistered channel `{channel_name}`")
        logger.info(f"Channel {interaction.channel.name} ({channel_id}) unregistered from {channel_name}")
    else:
        await interaction.response.send_message(
            "❌ You or this channel are not registered.",
            ephemeral=True
        )


@bot.tree.command(name="list", description="List all registered users and channels")
async def list_registered(interaction: discord.Interaction):
    """List all registered users and channels with their Discord names"""
    registrations = bot.registry.list_all()
    
    if not registrations:
        await interaction.response.send_message("📋 No registrations found.", ephemeral=True)
        return
    
    # Defer response as we might need to fetch user/channel info
    await interaction.response.defer(ephemeral=True)
    
    users = []
    channels = []
    
    for name, discord_id in sorted(registrations.items()):
        # Try to identify if it's a user or channel
        try:
            # Try to fetch as user
            user = await bot.fetch_user(int(discord_id))
            users.append((name, user.name, user.display_name))
        except (discord.NotFound, discord.HTTPException, ValueError):
            # Try to fetch as channel
            try:
                channel = await bot.fetch_channel(int(discord_id))
                channel_name = getattr(channel, 'name', 'Unknown Channel')
                channels.append((name, channel_name, discord_id))
            except (discord.NotFound, discord.HTTPException, ValueError):
                # Unknown or deleted entity
                channels.append((name, "Unknown/Deleted", discord_id))
    
    message = "📋 **Registered Names:**\n"
    
    if users:
        message += "\n**👤 Users:**\n"
        for reg_name, username, display_name in users:
            if username != display_name:
                message += f"• `{reg_name}` → @{username} ({display_name})\n"
            else:
                message += f"• `{reg_name}` → @{username}\n"
    
    if channels:
        message += "\n**💬 Channels:**\n"
        for reg_name, channel_name, channel_id in channels:
            message += f"• `{reg_name}` → #{channel_name}\n"
    
    if not users and not channels:
        message = "📋 No valid registrations found."
    
    await interaction.followup.send(message, ephemeral=True)


@bot.tree.command(name="example", description="Show an example of the MQTT payload format")
async def show_example(interaction: discord.Interaction):
    """Show an example of the MQTT payload format"""
    example = f"""
📨 **MQTT Message Example**

**Topic:** `{MQTT_TOPIC}`

**Payload (JSON):**
```json
{{
  "target_id": "your_registered_name",
  "message": "The front door has been opened.",
  "source": "Front Door Sensor"
}}
```

**Example using mosquitto_pub:**
```bash
mosquitto_pub -h <broker> -u <username> -P <password> \\
  -t "{MQTT_TOPIC}" \\
  -m '{{"target_id": "your_name", "message": "Hello from MQTT!", "source": "Test"}}'
```

**Fields:**
• `target_id` - The registered name (user or channel)
• `message` - The message content to send
• `source` - Where the message is coming from (optional, defaults to "Unknown")
"""
    await interaction.response.send_message(example, ephemeral=True)


@bot.tree.command(name="help", description="Show help information")
async def help_command(interaction: discord.Interaction):
    """Show help information"""
    help_text = """
🤖 **Discord MQTT Bot - Help**

**Registration:**
• `/register <name>` - Register yourself (in DM) or channel (in server) with a name
• `/unregister` - Unregister yourself or current channel
• `/list` - List all registered users and channels with their Discord names

**Information:**
• `/example` - Show MQTT payload example
• `/help` - Show this help message

**How it works:**
1. Use `/register` in a DM to register yourself, or in a channel to register that channel
2. External services send MQTT messages to the bot
3. Bot relays messages to registered users/channels
4. Names are shared between users and channels (no duplicates)

**Notes:**
• Only one name per user/channel
• Names must be unique across all registrations
• Messages persist through bot restarts
"""
    await interaction.response.send_message(help_text, ephemeral=True)


def main():
    """Main entry point"""
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not set in environment variables")
        return
    
    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")


if __name__ == "__main__":
    main()
