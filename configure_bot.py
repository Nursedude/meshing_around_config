#!/usr/bin/env python3
"""
Interactive Configuration Tool for Meshing-Around Bot
Helps configure alert settings and other bot parameters
"""

import os
import sys
import configparser
from pathlib import Path
from typing import Dict, List, Tuple, Any

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

def get_input(prompt: str, default: str = "", input_type: type = str) -> Any:
    """Get user input with optional default value"""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    while True:
        try:
            value = input(full_prompt).strip()
            if not value and default:
                value = default
            
            if input_type == bool:
                value_lower = value.lower()
                if value_lower in ['true', 'yes', 'y', '1', 'on']:
                    return True
                elif value_lower in ['false', 'no', 'n', '0', 'off']:
                    return False
                elif not value and default:
                    return default
                else:
                    print_error("Please enter yes/no (y/n) or true/false")
                    continue
            elif input_type == int:
                return int(value) if value else default
            elif input_type == float:
                return float(value) if value else default
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
    
    password = get_input("SMTP password")
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
    
    # Determine config file location
    default_config = "config.ini"
    config_file = get_input(f"Config file path", default_config)
    
    # Load or create config
    config = load_config(config_file)
    
    # Configuration wizard
    while True:
        print_section("Configuration Menu")
        print("1. Interface Settings (Serial/TCP/BLE)")
        print("2. General Settings (Bot name, admins)")
        print("3. Emergency Alerts")
        print("4. Proximity Alerts")
        print("5. Altitude Alerts")
        print("6. Weather Alerts")
        print("7. Battery Alerts")
        print("8. Noisy Node Detection")
        print("9. New Node Welcomes")
        print("10. Email/SMS Settings")
        print("11. Global Alert Settings")
        print("12. Save and Exit")
        print("13. Exit without Saving")
        
        choice = get_input("\nSelect option (1-13)", "12")
        
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
            save_config(config, config_file)
            print_success("\nConfiguration complete!")
            print(f"\nYou can now run the bot with: python3 mesh_bot.py")
            break
        elif choice == "13":
            if get_yes_no("Exit without saving changes?", False):
                print_warning("Exiting without saving")
                break
        else:
            print_error("Invalid choice, please try again")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print_warning("\n\nConfiguration cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"\nAn error occurred: {e}")
        sys.exit(1)
