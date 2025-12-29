#!/usr/bin/env python3
"""
Interactive Configuration Tool for Meshing-Around Bot
Helps configure alert settings and other bot parameters
"""

import os
import sys
import subprocess
import shutil
import re
import time
import configparser
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from getpass import getpass

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_section(text: str):
    """Print a section header"""
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-'*len(text)}{Colors.ENDC}")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")

def print_step(current: int, total: int, text: str):
    """Print step progress"""
    print(f"{Colors.OKCYAN}[{current}/{total}] {text}{Colors.ENDC}")

def run_command(cmd: List[str], desc: str = "", capture: bool = False, sudo: bool = False) -> Tuple[int, str, str]:
    """Run a shell command with optional sudo and output"""
    if sudo:
        cmd = ['sudo'] + cmd

    if desc:
        print_info(f"{desc}...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=600  # 10 minute timeout
        )
        stdout = result.stdout if capture else ""
        stderr = result.stderr if capture else ""
        return result.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        print_error(f"Command timed out: {' '.join(cmd)}")
        return -1, "", "Timeout"
    except FileNotFoundError:
        print_error(f"Command not found: {cmd[0]}")
        return -1, "", "Command not found"
    except Exception as e:
        print_error(f"Command failed: {e}")
        return -1, "", str(e)

def find_meshing_around() -> Optional[Path]:
    """Find the meshing-around installation directory"""
    common_paths = [
        Path.home() / "meshing-around",
        Path.home() / "mesh-bot",
        Path("/opt/meshing-around"),
        Path("/opt/mesh-bot"),
        Path.cwd().parent / "meshing-around",
        Path.cwd() / "meshing-around",
    ]

    for path in common_paths:
        if path.exists() and (path / "mesh_bot.py").exists():
            return path

    # Try to find it with locate or find
    try:
        result = subprocess.run(
            ['find', str(Path.home()), '-name', 'mesh_bot.py', '-type', 'f'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            bot_path = Path(result.stdout.strip().split('\n')[0]).parent
            return bot_path
    except:
        pass

    return None

def validate_mac_address(mac: str) -> bool:
    """Validate BLE MAC address format"""
    pattern = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
    return bool(re.match(pattern, mac))

def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude values"""
    return -90 <= lat <= 90 and -180 <= lon <= 180

def validate_port(port: str) -> bool:
    """Validate serial port exists"""
    return os.path.exists(port) or port.startswith('/dev/')

def get_input(prompt: str, default: str = "", input_type: type = str, password: bool = False) -> Any:
    """Get user input with optional default value and password masking"""
    if default:
        if password:
            full_prompt = f"{prompt} [****]: "
        else:
            full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "

    while True:
        try:
            if password:
                value = getpass(full_prompt)
            else:
                value = input(full_prompt).strip()

            if not value and default:
                value = str(default)

            if input_type == bool:
                value_lower = str(value).lower()
                if value_lower in ['true', 'yes', 'y', '1', 'on']:
                    return True
                elif value_lower in ['false', 'no', 'n', '0', 'off']:
                    return False
                else:
                    print_error("Please enter yes/no (y/n) or true/false")
                    continue
            elif input_type == int:
                return int(value) if value else int(default) if default else 0
            elif input_type == float:
                return float(value) if value else float(default) if default else 0.0
            else:
                return value
        except ValueError:
            print_error(f"Invalid input. Expected {input_type.__name__}")

def get_yes_no(prompt: str, default: bool = False) -> bool:
    """Get yes/no input from user"""
    default_str = "Y/n" if default else "y/N"
    response = get_input(f"{prompt} ({default_str})", "y" if default else "n")
    return response.lower() in ['y', 'yes', 'true', '1']

def configure_interface(config: configparser.ConfigParser):
    """Configure interface settings"""
    print_section("Interface Configuration")
    
    print("\nConnection types:")
    print("  1. Serial (recommended)")
    print("  2. TCP")
    print("  3. BLE")
    
    conn_type = get_input("Select connection type (1-3)", "1")
    type_map = {"1": "serial", "2": "tcp", "3": "ble"}
    conn_type_str = type_map.get(conn_type, "serial")
    
    config['interface']['type'] = conn_type_str
    
    if conn_type_str == "serial":
        use_auto = get_yes_no("Use auto-detect for serial port?", True)
        if not use_auto:
            port = get_input("Enter serial port", "/dev/ttyUSB0")
            config['interface']['port'] = port
    elif conn_type_str == "tcp":
        hostname = get_input("Enter TCP hostname/IP", "192.168.1.100")
        config['interface']['hostname'] = hostname
    elif conn_type_str == "ble":
        mac = get_input("Enter BLE MAC address", "AA:BB:CC:DD:EE:FF")
        config['interface']['mac'] = mac
    
    print_success(f"Interface configured: {conn_type_str}")

def configure_general(config: configparser.ConfigParser):
    """Configure general settings"""
    print_section("General Settings")
    
    bot_name = get_input("Bot name", "MeshBot")
    config['general']['bot_name'] = bot_name
    
    if get_yes_no("Configure admin nodes?", False):
        admin_list = get_input("Admin node numbers (comma-separated)")
        config['general']['bbs_admin_list'] = admin_list
    
    if get_yes_no("Configure favorite nodes?", False):
        fav_list = get_input("Favorite node numbers (comma-separated)")
        config['general']['favoriteNodeList'] = fav_list
    
    print_success("General settings configured")

def configure_emergency_alerts(config: configparser.ConfigParser):
    """Configure emergency alert settings"""
    print_section("Emergency Alert Configuration")
    
    if not get_yes_no("Enable emergency keyword detection?", True):
        config['emergencyHandler']['enabled'] = 'False'
        return
    
    config['emergencyHandler']['enabled'] = 'True'
    
    print("\nDefault keywords: emergency, 911, 112, 999, police, fire, ambulance, rescue, help, sos, mayday")
    if get_yes_no("Use default emergency keywords?", True):
        config['emergencyHandler']['emergency_keywords'] = 'emergency,911,112,999,police,fire,ambulance,rescue,help,sos,mayday'
    else:
        keywords = get_input("Enter emergency keywords (comma-separated)")
        config['emergencyHandler']['emergency_keywords'] = keywords
    
    channel = get_input("Alert channel number", "2", int)
    config['emergencyHandler']['alert_channel'] = str(channel)
    
    cooldown = get_input("Cooldown period between alerts (seconds)", "300", int)
    config['emergencyHandler']['cooldown_period'] = str(cooldown)
    
    if get_yes_no("Enable email notifications for emergencies?", False):
        config['emergencyHandler']['send_email'] = 'True'
    
    if get_yes_no("Enable SMS notifications for emergencies?", False):
        config['emergencyHandler']['send_sms'] = 'True'
    
    if get_yes_no("Play sound for emergency alerts?", False):
        config['emergencyHandler']['play_sound'] = 'True'
        sound_file = get_input("Sound file path", "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga")
        config['emergencyHandler']['sound_file'] = sound_file
    
    print_success("Emergency alerts configured")

def configure_proximity_alerts(config: configparser.ConfigParser):
    """Configure proximity-based alerts"""
    print_section("Proximity Alert Configuration")
    
    print("\nProximity alerts notify when nodes enter a specified area")
    print("Useful for campsite monitoring, geofencing, etc.")
    
    if not get_yes_no("Enable proximity alerts?", False):
        config['proximityAlert']['enabled'] = 'False'
        return
    
    config['proximityAlert']['enabled'] = 'True'
    
    lat = get_input("Target latitude", "0.0", float)
    config['proximityAlert']['target_latitude'] = str(lat)
    
    lon = get_input("Target longitude", "0.0", float)
    config['proximityAlert']['target_longitude'] = str(lon)
    
    radius = get_input("Proximity radius in meters", "100", int)
    config['proximityAlert']['radius_meters'] = str(radius)
    
    channel = get_input("Alert channel", "0", int)
    config['proximityAlert']['alert_channel'] = str(channel)
    
    interval = get_input("Check interval in seconds", "60", int)
    config['proximityAlert']['check_interval'] = str(interval)
    
    if get_yes_no("Execute script on proximity trigger?", False):
        config['proximityAlert']['run_script'] = 'True'
        script_path = get_input("Script path")
        config['proximityAlert']['script_path'] = script_path
    
    print_success("Proximity alerts configured")

def configure_altitude_alerts(config: configparser.ConfigParser):
    """Configure high altitude alerts"""
    print_section("Altitude Alert Configuration")
    
    if not get_yes_no("Enable high altitude detection?", False):
        config['altitudeAlert']['enabled'] = 'False'
        return
    
    config['altitudeAlert']['enabled'] = 'True'
    
    altitude = get_input("Minimum altitude threshold (meters)", "1000", int)
    config['altitudeAlert']['min_altitude'] = str(altitude)
    
    channel = get_input("Alert channel", "0", int)
    config['altitudeAlert']['alert_channel'] = str(channel)
    
    interval = get_input("Check interval (seconds)", "120", int)
    config['altitudeAlert']['check_interval'] = str(interval)
    
    print_success("Altitude alerts configured")

def configure_weather_alerts(config: configparser.ConfigParser):
    """Configure weather/NOAA alerts"""
    print_section("Weather Alert Configuration")
    
    if not get_yes_no("Enable weather/NOAA alerts?", False):
        config['weatherAlert']['enabled'] = 'False'
        return
    
    config['weatherAlert']['enabled'] = 'True'
    
    location = get_input("Location (latitude,longitude)")
    config['weatherAlert']['location'] = location
    
    print("\nSeverity levels: Extreme, Severe, Moderate, Minor")
    severity = get_input("Alert severity levels (comma-separated)", "Extreme,Severe")
    config['weatherAlert']['severity_levels'] = severity
    
    interval = get_input("Check interval (minutes)", "30", int)
    config['weatherAlert']['check_interval_minutes'] = str(interval)
    
    channel = get_input("Alert channel", "2", int)
    config['weatherAlert']['alert_channel'] = str(channel)
    
    print_success("Weather alerts configured")

def configure_battery_alerts(config: configparser.ConfigParser):
    """Configure low battery alerts"""
    print_section("Battery Alert Configuration")
    
    if not get_yes_no("Enable low battery monitoring?", False):
        config['batteryAlert']['enabled'] = 'False'
        return
    
    config['batteryAlert']['enabled'] = 'True'
    
    threshold = get_input("Battery threshold percentage", "20", int)
    config['batteryAlert']['threshold_percent'] = str(threshold)
    
    interval = get_input("Check interval (minutes)", "30", int)
    config['batteryAlert']['check_interval_minutes'] = str(interval)
    
    channel = get_input("Alert channel", "0", int)
    config['batteryAlert']['alert_channel'] = str(channel)
    
    if get_yes_no("Monitor specific nodes only?", False):
        nodes = get_input("Node numbers to monitor (comma-separated)")
        config['batteryAlert']['monitor_nodes'] = nodes
    
    print_success("Battery alerts configured")

def configure_noisy_node_alerts(config: configparser.ConfigParser):
    """Configure noisy node detection"""
    print_section("Noisy Node Alert Configuration")
    
    if not get_yes_no("Enable noisy node detection?", False):
        config['noisyNodeAlert']['enabled'] = 'False'
        return
    
    config['noisyNodeAlert']['enabled'] = 'True'
    
    threshold = get_input("Message threshold (messages per period)", "50", int)
    config['noisyNodeAlert']['message_threshold'] = str(threshold)
    
    period = get_input("Time period (minutes)", "10", int)
    config['noisyNodeAlert']['time_period_minutes'] = str(period)
    
    if get_yes_no("Auto-mute noisy nodes?", False):
        config['noisyNodeAlert']['auto_mute'] = 'True'
        duration = get_input("Mute duration (minutes)", "60", int)
        config['noisyNodeAlert']['mute_duration_minutes'] = str(duration)
    
    print_success("Noisy node alerts configured")

def configure_new_node_alerts(config: configparser.ConfigParser):
    """Configure new node welcome messages"""
    print_section("New Node Alert Configuration")
    
    if not get_yes_no("Enable new node welcomes?", True):
        config['newNodeAlert']['enabled'] = 'False'
        return
    
    config['newNodeAlert']['enabled'] = 'True'
    
    message = get_input("Welcome message (use {node_name} placeholder)", "Welcome to the mesh, {node_name}!")
    config['newNodeAlert']['welcome_message'] = message
    
    send_dm = get_yes_no("Send welcome as DM?", True)
    config['newNodeAlert']['send_as_dm'] = str(send_dm)
    
    if get_yes_no("Also announce to channel?", False):
        config['newNodeAlert']['announce_to_channel'] = 'True'
        channel = get_input("Announcement channel", "0", int)
        config['newNodeAlert']['announcement_channel'] = str(channel)
    
    print_success("New node alerts configured")

def configure_email_sms(config: configparser.ConfigParser):
    """Configure email and SMS settings"""
    print_section("Email/SMS Configuration")
    
    if not get_yes_no("Configure email settings?", False):
        return
    
    config['smtp']['enableSMTP'] = 'True'
    
    server = get_input("SMTP server", "smtp.gmail.com")
    config['smtp']['SMTP_SERVER'] = server
    
    port = get_input("SMTP port", "587", int)
    config['smtp']['SMTP_PORT'] = str(port)
    
    username = get_input("SMTP username/email")
    config['smtp']['SMTP_USERNAME'] = username
    
    password = get_input("SMTP password", password=True)
    config['smtp']['SMTP_PASSWORD'] = password
    
    from_addr = get_input("From email address", username)
    config['smtp']['SMTP_FROM'] = from_addr
    
    sysop_emails = get_input("Sysop email addresses (comma-separated)")
    config['smtp']['sysopEmails'] = sysop_emails
    
    if get_yes_no("Configure SMS settings?", False):
        config['sms']['enabled'] = 'True'
        gateway = get_input("SMS gateway (e.g., @txt.att.net)")
        config['sms']['gateway'] = gateway
        phones = get_input("Phone numbers (comma-separated)")
        config['sms']['phone_numbers'] = phones
    
    print_success("Email/SMS settings configured")

def configure_global_settings(config: configparser.ConfigParser):
    """Configure global alert settings"""
    print_section("Global Alert Settings")

    if get_yes_no("Enable all alerts globally?", True):
        config['alertGlobal']['global_enabled'] = 'True'
    else:
        config['alertGlobal']['global_enabled'] = 'False'
        return

    if get_yes_no("Configure quiet hours?", False):
        quiet = get_input("Quiet hours (24hr format HH:MM-HH:MM, e.g., 22:00-07:00)")
        config['alertGlobal']['quiet_hours'] = quiet

    max_rate = get_input("Maximum alerts per hour (all types)", "20", int)
    config['alertGlobal']['max_alerts_per_hour'] = str(max_rate)

    print_success("Global settings configured")


# ============================================================================
# SYSTEM MAINTENANCE FUNCTIONS
# ============================================================================

def system_update() -> bool:
    """Run apt update and upgrade"""
    print_section("System Update")
    print_info("This will update your system packages (requires sudo)")

    if not get_yes_no("Proceed with system update?", True):
        print_warning("Skipping system update")
        return True

    errors = []

    # Step 1: apt update
    print_step(1, 3, "Updating package lists...")
    ret, stdout, stderr = run_command(['apt', 'update'], sudo=True)
    if ret != 0:
        errors.append(f"apt update failed: {stderr}")
        print_error("Failed to update package lists")
    else:
        print_success("Package lists updated")

    # Step 2: apt upgrade
    print_step(2, 3, "Upgrading packages...")
    ret, stdout, stderr = run_command(['apt', 'upgrade', '-y'], sudo=True)
    if ret != 0:
        errors.append(f"apt upgrade failed: {stderr}")
        print_error("Failed to upgrade packages")
    else:
        print_success("Packages upgraded")

    # Step 3: Clean up
    print_step(3, 3, "Cleaning up...")
    run_command(['apt', 'autoremove', '-y'], sudo=True)
    print_success("Cleanup complete")

    if errors:
        print_warning("Some errors occurred during update:")
        for err in errors:
            print_error(f"  {err}")
        return False

    print_success("System update completed successfully!")
    return True


def update_meshing_around(meshing_path: Optional[Path] = None) -> Tuple[bool, Optional[Path]]:
    """Git pull the latest meshing-around code"""
    print_section("Update Meshing-Around")

    # Find meshing-around directory
    if meshing_path is None:
        meshing_path = find_meshing_around()

    if meshing_path is None:
        print_warning("Meshing-around not found in common locations")
        custom_path = get_input("Enter path to meshing-around directory (or 'skip')")
        if custom_path.lower() == 'skip':
            return True, None
        meshing_path = Path(custom_path)

    if not meshing_path.exists():
        print_error(f"Directory not found: {meshing_path}")
        if get_yes_no("Clone meshing-around from GitHub?", True):
            clone_path = get_input("Clone to directory", str(Path.home() / "meshing-around"))
            ret, _, stderr = run_command(
                ['git', 'clone', 'https://github.com/SpudGunMan/meshing-around.git', clone_path],
                desc="Cloning meshing-around"
            )
            if ret == 0:
                print_success(f"Cloned to {clone_path}")
                meshing_path = Path(clone_path)
            else:
                print_error(f"Clone failed: {stderr}")
                return False, None
        else:
            return True, None

    print_info(f"Found meshing-around at: {meshing_path}")

    # Git pull
    print_info("Pulling latest changes...")
    original_dir = os.getcwd()
    try:
        os.chdir(meshing_path)

        # Check for uncommitted changes
        ret, stdout, _ = run_command(['git', 'status', '--porcelain'], capture=True)
        if stdout.strip():
            print_warning("Uncommitted changes detected:")
            print(stdout)
            if not get_yes_no("Continue with git pull anyway?", False):
                os.chdir(original_dir)
                return True, meshing_path

        # Git pull
        ret, stdout, stderr = run_command(['git', 'pull', 'origin', 'main'], capture=True)
        if ret != 0:
            # Try master branch
            ret, stdout, stderr = run_command(['git', 'pull', 'origin', 'master'], capture=True)

        if ret == 0:
            if 'Already up to date' in stdout:
                print_success("Already up to date")
            else:
                print_success("Updated to latest version")
                print(stdout)
        else:
            print_error(f"Git pull failed: {stderr}")
            os.chdir(original_dir)
            return False, meshing_path

    finally:
        os.chdir(original_dir)

    return True, meshing_path


def install_dependencies(meshing_path: Path) -> bool:
    """Install Python dependencies for meshing-around"""
    print_section("Install Dependencies")

    requirements_file = meshing_path / "requirements.txt"
    if not requirements_file.exists():
        print_warning("No requirements.txt found")
        return True

    if not get_yes_no("Install Python dependencies?", True):
        return True

    print_info("Installing Python dependencies...")
    ret, stdout, stderr = run_command(
        ['pip3', 'install', '-r', str(requirements_file)],
        desc="Installing dependencies"
    )

    if ret != 0:
        print_error(f"Failed to install dependencies: {stderr}")
        print_warning("Try running: pip3 install -r requirements.txt manually")
        return False

    print_success("Dependencies installed")
    return True


def verify_bot_running(meshing_path: Path) -> bool:
    """Verify that the meshing-around bot can run"""
    print_section("Verify Bot")

    bot_script = meshing_path / "mesh_bot.py"
    if not bot_script.exists():
        print_error(f"mesh_bot.py not found at {meshing_path}")
        return False

    # Check if bot is already running
    ret, stdout, _ = run_command(['pgrep', '-f', 'mesh_bot.py'], capture=True)
    if ret == 0 and stdout.strip():
        print_success("Bot is already running!")
        print_info(f"PID(s): {stdout.strip()}")
        return True

    # Test if bot can start (syntax check)
    print_info("Checking bot syntax...")
    ret, stdout, stderr = run_command(
        ['python3', '-m', 'py_compile', str(bot_script)],
        capture=True
    )
    if ret != 0:
        print_error(f"Syntax error in bot: {stderr}")
        return False
    print_success("Bot syntax OK")

    # Check for config file
    config_locations = [
        meshing_path / "config.ini",
        meshing_path / "config.yaml",
        meshing_path / "config.yml"
    ]
    config_found = any(c.exists() for c in config_locations)
    if not config_found:
        print_warning("No config file found in meshing-around directory")
        print_info("Run this configurator and copy config.ini to meshing-around directory")

    # Try to start the bot
    if get_yes_no("Start the bot now?", True):
        print_info("Starting mesh_bot.py...")
        original_dir = os.getcwd()
        try:
            os.chdir(meshing_path)

            # Start in background
            process = subprocess.Popen(
                ['python3', 'mesh_bot.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            # Wait a few seconds to see if it crashes
            time.sleep(3)

            if process.poll() is None:
                print_success(f"Bot started successfully! PID: {process.pid}")
                print_info("Bot is running in the background")
                return True
            else:
                stdout, stderr = process.communicate()
                print_error("Bot failed to start:")
                if stderr:
                    print(stderr.decode())
                if stdout:
                    print(stdout.decode())
                return False

        except Exception as e:
            print_error(f"Failed to start bot: {e}")
            return False
        finally:
            os.chdir(original_dir)

    return True


def quick_setup():
    """Quick setup wizard for first-time users"""
    print_header("Quick Setup Wizard")

    print("""
This wizard will:
  1. Update your system (apt update/upgrade)
  2. Find or clone meshing-around
  3. Install dependencies
  4. Create a basic configuration
  5. Verify the bot can run
""")

    if not get_yes_no("Continue with quick setup?", True):
        return None

    errors = []

    # Step 1: System update
    print_step(1, 5, "System Update")
    if not system_update():
        errors.append("System update had issues")

    # Step 2: Find/update meshing-around
    print_step(2, 5, "Meshing-Around Setup")
    success, meshing_path = update_meshing_around()
    if not success:
        errors.append("Failed to update meshing-around")

    # Step 3: Install dependencies
    if meshing_path:
        print_step(3, 5, "Install Dependencies")
        if not install_dependencies(meshing_path):
            errors.append("Dependency installation had issues")

    # Step 4: Create basic config
    print_step(4, 5, "Create Configuration")
    config = create_basic_config()

    # Step 5: Verify bot
    if meshing_path:
        print_step(5, 5, "Verify Bot")
        if not verify_bot_running(meshing_path):
            errors.append("Bot verification failed")

    # Summary
    print_section("Setup Summary")
    if errors:
        print_warning("Setup completed with some issues:")
        for err in errors:
            print_error(f"  • {err}")
    else:
        print_success("Setup completed successfully!")

    if meshing_path:
        print_info(f"Meshing-around location: {meshing_path}")
        print_info("Next steps:")
        print(f"  1. Copy config.ini to {meshing_path}/")
        print(f"  2. cd {meshing_path}")
        print("  3. python3 mesh_bot.py")

    return config


def create_basic_config() -> configparser.ConfigParser:
    """Create a basic configuration interactively"""
    print_section("Basic Configuration")

    config = configparser.ConfigParser()

    # Initialize all sections
    sections = [
        'interface', 'general', 'emergencyHandler', 'proximityAlert',
        'altitudeAlert', 'weatherAlert', 'ipawsAlert', 'volcanoAlert',
        'noisyNodeAlert', 'batteryAlert', 'newNodeAlert', 'snrAlert',
        'disconnectAlert', 'customAlert', 'alertGlobal', 'smtp', 'sms'
    ]
    for section in sections:
        config.add_section(section)

    # Basic interface config
    configure_interface(config)

    # Basic general config
    configure_general(config)

    # Enable emergency alerts by default
    config['emergencyHandler']['enabled'] = 'True'
    config['emergencyHandler']['emergency_keywords'] = 'emergency,911,112,999,sos,help,mayday'
    config['emergencyHandler']['alert_channel'] = '2'
    print_success("Emergency alerts enabled with default keywords")

    # Enable new node welcomes
    config['newNodeAlert']['enabled'] = 'True'
    config['newNodeAlert']['welcome_message'] = 'Welcome to the mesh!'
    print_success("New node welcomes enabled")

    # Global settings
    config['alertGlobal']['global_enabled'] = 'True'

    return config


def show_system_info():
    """Display system information"""
    print_section("System Information")

    # OS Info
    ret, stdout, _ = run_command(['uname', '-a'], capture=True)
    if ret == 0:
        print(f"System: {stdout.strip()}")

    # Python version
    print(f"Python: {sys.version.split()[0]}")

    # Check for meshtastic library
    try:
        import meshtastic
        print(f"Meshtastic library: {meshtastic.__version__ if hasattr(meshtastic, '__version__') else 'installed'}")
    except ImportError:
        print_warning("Meshtastic library: NOT INSTALLED")
        print_info("  Install with: pip3 install meshtastic")

    # Check for serial ports
    print("\nAvailable serial ports:")
    ret, stdout, _ = run_command(['ls', '-la', '/dev/ttyUSB*'], capture=True)
    if ret == 0:
        print(stdout)
    else:
        ret, stdout, _ = run_command(['ls', '-la', '/dev/ttyACM*'], capture=True)
        if ret == 0:
            print(stdout)
        else:
            print_warning("  No USB serial ports found")

    # Check for meshing-around
    meshing_path = find_meshing_around()
    if meshing_path:
        print(f"\nMeshing-around found: {meshing_path}")
    else:
        print_warning("\nMeshing-around: NOT FOUND")

    # Disk space
    ret, stdout, _ = run_command(['df', '-h', '/'], capture=True)
    if ret == 0:
        print(f"\nDisk space:\n{stdout}")

def load_config(config_file: str) -> configparser.ConfigParser:
    """Load existing config or create new one"""
    config = configparser.ConfigParser()
    
    if os.path.exists(config_file):
        print_success(f"Loading existing config from {config_file}")
        config.read(config_file)
    else:
        print_warning(f"No existing config found, creating new configuration")
        # Initialize sections
        sections = [
            'interface', 'general', 'emergencyHandler', 'proximityAlert',
            'altitudeAlert', 'weatherAlert', 'ipawsAlert', 'volcanoAlert',
            'noisyNodeAlert', 'batteryAlert', 'newNodeAlert', 'snrAlert',
            'disconnectAlert', 'customAlert', 'alertGlobal', 'smtp', 'sms'
        ]
        for section in sections:
            if not config.has_section(section):
                config.add_section(section)
    
    return config

def save_config(config: configparser.ConfigParser, config_file: str):
    """Save configuration to file"""
    try:
        with open(config_file, 'w') as f:
            config.write(f)
        print_success(f"\nConfiguration saved to {config_file}")
    except Exception as e:
        print_error(f"Failed to save config: {e}")
        sys.exit(1)

def main_menu():
    """Display main menu and handle user selection"""
    print_header("Meshing-Around Interactive Configuration Tool")

    print("\nThis tool will help you configure your Meshtastic bot")
    print("You can configure alert settings, connection parameters, and more\n")

    # Show startup menu
    print_section("Start Menu")
    print("1. Quick Setup (recommended for first-time users)")
    print("2. Advanced Configuration")
    print("3. System Maintenance Only")
    print("4. Show System Info")
    print("5. Exit")

    start_choice = get_input("\nSelect option (1-5)", "1")

    if start_choice == "1":
        config = quick_setup()
        if config:
            config_file = get_input("Save config to", "config.ini")
            save_config(config, config_file)
        return
    elif start_choice == "3":
        system_maintenance_menu()
        return
    elif start_choice == "4":
        show_system_info()
        if get_yes_no("\nContinue to configuration?", True):
            pass
        else:
            return
    elif start_choice == "5":
        print_success("Goodbye!")
        return

    # Determine config file location
    default_config = "config.ini"
    config_file = get_input(f"Config file path", default_config)

    # Load or create config
    config = load_config(config_file)

    # Track meshing-around path
    meshing_path = find_meshing_around()

    # Configuration wizard
    while True:
        print_section("Configuration Menu")
        print(f"{Colors.BOLD}--- Alert Configuration ---{Colors.ENDC}")
        print("1.  Interface Settings (Serial/TCP/BLE)")
        print("2.  General Settings (Bot name, admins)")
        print("3.  Emergency Alerts")
        print("4.  Proximity Alerts")
        print("5.  Altitude Alerts")
        print("6.  Weather Alerts")
        print("7.  Battery Alerts")
        print("8.  Noisy Node Detection")
        print("9.  New Node Welcomes")
        print("10. Email/SMS Settings")
        print("11. Global Alert Settings")
        print(f"\n{Colors.BOLD}--- System Maintenance ---{Colors.ENDC}")
        print("12. System Update (apt update/upgrade)")
        print("13. Update Meshing-Around (git pull)")
        print("14. Install Dependencies")
        print("15. Verify Bot Running")
        print("16. Show System Info")
        print(f"\n{Colors.BOLD}--- Save & Exit ---{Colors.ENDC}")
        print("17. Save and Exit")
        print("18. Save, Deploy & Start Bot")
        print("19. Exit without Saving")

        choice = get_input("\nSelect option (1-19)", "17")

        if choice == "1":
            configure_interface(config)
        elif choice == "2":
            configure_general(config)
        elif choice == "3":
            configure_emergency_alerts(config)
        elif choice == "4":
            configure_proximity_alerts(config)
        elif choice == "5":
            configure_altitude_alerts(config)
        elif choice == "6":
            configure_weather_alerts(config)
        elif choice == "7":
            configure_battery_alerts(config)
        elif choice == "8":
            configure_noisy_node_alerts(config)
        elif choice == "9":
            configure_new_node_alerts(config)
        elif choice == "10":
            configure_email_sms(config)
        elif choice == "11":
            configure_global_settings(config)
        elif choice == "12":
            system_update()
        elif choice == "13":
            success, meshing_path = update_meshing_around(meshing_path)
        elif choice == "14":
            if meshing_path:
                install_dependencies(meshing_path)
            else:
                print_error("Meshing-around not found. Run option 13 first.")
        elif choice == "15":
            if meshing_path:
                verify_bot_running(meshing_path)
            else:
                print_error("Meshing-around not found. Run option 13 first.")
        elif choice == "16":
            show_system_info()
        elif choice == "17":
            save_config(config, config_file)
            print_success("\nConfiguration complete!")
            if meshing_path:
                print_info(f"Copy config to: {meshing_path}/config.ini")
            print(f"\nRun the bot with: python3 mesh_bot.py")
            break
        elif choice == "18":
            save_config(config, config_file)
            if meshing_path:
                deploy_and_start(config_file, meshing_path)
            else:
                print_error("Meshing-around not found. Configure path first.")
            break
        elif choice == "19":
            if get_yes_no("Exit without saving changes?", False):
                print_warning("Exiting without saving")
                break
        else:
            print_error("Invalid choice, please try again")


def system_maintenance_menu():
    """Menu for system maintenance only"""
    print_header("System Maintenance")

    meshing_path = find_meshing_around()

    while True:
        print_section("Maintenance Menu")
        print("1. System Update (apt update/upgrade)")
        print("2. Update Meshing-Around (git pull)")
        print("3. Install Dependencies")
        print("4. Verify Bot Running")
        print("5. Show System Info")
        print("6. Run All Maintenance")
        print("7. Back to Main Menu")

        choice = get_input("\nSelect option (1-7)", "6")

        if choice == "1":
            system_update()
        elif choice == "2":
            success, meshing_path = update_meshing_around(meshing_path)
        elif choice == "3":
            if meshing_path:
                install_dependencies(meshing_path)
            else:
                print_error("Meshing-around not found. Run option 2 first.")
        elif choice == "4":
            if meshing_path:
                verify_bot_running(meshing_path)
            else:
                print_error("Meshing-around not found. Run option 2 first.")
        elif choice == "5":
            show_system_info()
        elif choice == "6":
            # Run all maintenance
            print_section("Running All Maintenance")
            system_update()
            success, meshing_path = update_meshing_around(meshing_path)
            if meshing_path:
                install_dependencies(meshing_path)
                verify_bot_running(meshing_path)
            print_success("Maintenance complete!")
        elif choice == "7":
            break
        else:
            print_error("Invalid choice")


def deploy_and_start(config_file: str, meshing_path: Path):
    """Deploy config and start the bot"""
    print_section("Deploy and Start")

    # Copy config to meshing-around directory
    dest_config = meshing_path / "config.ini"
    try:
        shutil.copy(config_file, dest_config)
        print_success(f"Config deployed to {dest_config}")
    except Exception as e:
        print_error(f"Failed to copy config: {e}")
        return

    # Start the bot
    verify_bot_running(meshing_path)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print_warning("\n\nConfiguration cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"\nAn error occurred: {e}")
        sys.exit(1)
