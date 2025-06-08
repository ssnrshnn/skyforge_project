#!/bin/bash

# Raspberry Pi Weather Display System - Automated Setup Script
# This script automates the complete installation and configuration process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
PROJECT_DIR="/home/pi/weather-display"
SERVICE_NAME="weather-display"
FONT_DIR="/usr/share/fonts/truetype"
CURRENT_USER=$(whoami)

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root. Please run as a regular user."
        print_error "The script will ask for sudo password when needed."
        exit 1
    fi
}

# Function to check if running on Raspberry Pi
check_raspberry_pi() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_warning "This doesn't appear to be a Raspberry Pi."
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Installation cancelled."
            exit 1
        fi
    fi
}

# Function to update system packages
update_system() {
    print_status "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    print_success "System packages updated successfully"
}

# Function to install system dependencies
install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    local packages=(
        "python3"
        "python3-pip"
        "python3-dev"
        "git"
        "fontconfig"
        "libjpeg-dev"
        "zlib1g-dev"
        "libfreetype6-dev"
        "liblcms2-dev"
        "libopenjp2-7"
        "libtiff5"
    )
    
    for package in "${packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            print_status "Installing $package..."
            sudo apt install -y "$package"
        else
            print_status "$package is already installed"
        fi
    done
    
    print_success "System dependencies installed successfully"
}

# Function to install Python dependencies
install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    local pip_packages=(
        "requests"
        "pillow"
        "adafruit-circuitpython-rgb-display"
        "RPi.GPIO"
        "adafruit-blinka"
    )
    
    for package in "${pip_packages[@]}"; do
        print_status "Installing Python package: $package"
        pip3 install --user "$package"
    done
    
    print_success "Python dependencies installed successfully"
}

# Function to enable SPI interface
enable_spi() {
    print_status "Checking SPI interface status..."
    
    if ! lsmod | grep -q spi_bcm2835; then
        print_status "Enabling SPI interface..."
        sudo raspi-config nonint do_spi 0
        print_success "SPI interface enabled"
        print_warning "A reboot will be required after setup completion"
    else
        print_success "SPI interface is already enabled"
    fi
}

# Function to create project directory
create_project_directory() {
    print_status "Creating project directory..."
    
    if [[ ! -d "$PROJECT_DIR" ]]; then
        mkdir -p "$PROJECT_DIR"
        print_success "Project directory created: $PROJECT_DIR"
    else
        print_status "Project directory already exists: $PROJECT_DIR"
    fi
}

# Function to copy project files
copy_project_files() {
    print_status "Copying project files..."
    
    local files=("main.py" "a.py" "b.py" "Orbitron-Bold.ttf" "weather-display.service")
    local current_dir=$(pwd)
    
    for file in "${files[@]}"; do
        if [[ -f "$current_dir/$file" ]]; then
            cp "$current_dir/$file" "$PROJECT_DIR/"
            print_success "Copied $file to project directory"
        else
            print_error "File not found: $file"
            print_error "Please ensure all project files are in the current directory"
            exit 1
        fi
    done
}

# Function to install font
install_font() {
    print_status "Installing Orbitron font..."
    
    if [[ -f "$PROJECT_DIR/Orbitron-Bold.ttf" ]]; then
        sudo mkdir -p "$FONT_DIR"
        sudo cp "$PROJECT_DIR/Orbitron-Bold.ttf" "$FONT_DIR/"
        sudo fc-cache -fv > /dev/null 2>&1
        print_success "Orbitron font installed successfully"
    else
        print_error "Font file not found: $PROJECT_DIR/Orbitron-Bold.ttf"
        exit 1
    fi
}

# Function to setup systemd service
setup_systemd_service() {
    print_status "Setting up systemd service..."
    
    # Update service file with correct paths and user
    sed -i "s|User=pi|User=$CURRENT_USER|g" "$PROJECT_DIR/weather-display.service"
    sed -i "s|WorkingDirectory=/home/pi|WorkingDirectory=$PROJECT_DIR|g" "$PROJECT_DIR/weather-display.service"
    sed -i "s|ExecStart=/usr/bin/python3 /home/pi/main.py|ExecStart=/usr/bin/python3 $PROJECT_DIR/main.py|g" "$PROJECT_DIR/weather-display.service"
    
    # Copy service file and enable it
    sudo cp "$PROJECT_DIR/weather-display.service" "/etc/systemd/system/"
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME.service"
    
    print_success "Systemd service configured and enabled"
}

# Function to set up API key
setup_api_key() {
    print_status "Setting up Weather API..."
    
    echo
    print_warning "This project requires a free OpenWeatherMap API key to function."
    print_warning "You can get your free API key from: https://openweathermap.org/api"
    print_warning "The API key is completely free for up to 1000 calls per day."
    echo
    
    while true; do
        read -p "Please enter your OpenWeatherMap API key: " api_key
        
        if [[ -n "$api_key" && "$api_key" != "YOUR_API_KEY_HERE" ]]; then
            sed -i "s/WEATHER_API_KEY = \"YOUR_API_KEY_HERE\"/WEATHER_API_KEY = \"$api_key\"/" "$PROJECT_DIR/a.py"
            print_success "API key configured successfully"
            break
        else
            print_error "Please enter a valid API key. You can get one free from:"
            print_error "https://openweathermap.org/api"
            echo
            read -p "Do you want to continue without setting the API key? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                print_warning "API key not set. The weather display will not work until you manually"
                print_warning "edit $PROJECT_DIR/a.py and replace YOUR_API_KEY_HERE with your actual API key"
                break
            fi
        fi
    done
}

# Function to test hardware connections
test_hardware() {
    print_status "Testing hardware connections..."
    
    echo
    print_warning "Hardware Test Mode"
    print_warning "Make sure your hardware is connected according to the README.md"
    echo
    
    read -p "Do you want to run a quick hardware test? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Running LED test..."
        
        # Create a simple LED test script
        cat > "$PROJECT_DIR/test_leds.py" << 'EOF'
#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import sys

LED1_PIN = 17  # Green LED
LED2_PIN = 27  # Red LED

try:
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED1_PIN, GPIO.OUT)
    GPIO.setup(LED2_PIN, GPIO.OUT)
    
    print("Testing LEDs... (Press Ctrl+C to stop)")
    
    for i in range(5):
        print(f"Blink cycle {i+1}/5")
        GPIO.output(LED1_PIN, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(LED1_PIN, GPIO.LOW)
        GPIO.output(LED2_PIN, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(LED2_PIN, GPIO.LOW)
        time.sleep(0.5)
    
    print("LED test completed successfully!")
    
except KeyboardInterrupt:
    print("\nTest interrupted by user")
except Exception as e:
    print(f"LED test failed: {e}")
    sys.exit(1)
finally:
    GPIO.cleanup()
EOF
        
        python3 "$PROJECT_DIR/test_leds.py"
        rm "$PROJECT_DIR/test_leds.py"
        
        print_success "Hardware test completed"
    else
        print_status "Skipping hardware test"
    fi
}

# Function to start the service
start_service() {
    print_status "Starting weather display service..."
    
    if sudo systemctl start "$SERVICE_NAME.service"; then
        print_success "Service started successfully"
        
        # Wait a moment and check status
        sleep 3
        if sudo systemctl is-active --quiet "$SERVICE_NAME.service"; then
            print_success "Service is running properly"
        else
            print_warning "Service may have issues. Check logs with:"
            print_warning "sudo journalctl -u $SERVICE_NAME.service -f"
        fi
    else
        print_error "Failed to start service"
        return 1
    fi
}

# Function to display final instructions
display_final_instructions() {
    echo
    print_success "=== INSTALLATION COMPLETED SUCCESSFULLY ==="
    echo
    print_status "Your Raspberry Pi Weather Display System is now installed and running!"
    echo
    print_status "Useful commands:"
    echo "  • Check service status: sudo systemctl status $SERVICE_NAME.service"
    echo "  • View logs: sudo journalctl -u $SERVICE_NAME.service -f"
    echo "  • Stop service: sudo systemctl stop $SERVICE_NAME.service"
    echo "  • Start service: sudo systemctl start $SERVICE_NAME.service"
    echo "  • Restart service: sudo systemctl restart $SERVICE_NAME.service"
    echo
    print_status "Project files are located in: $PROJECT_DIR"
    echo
    
    if lsmod | grep -q spi_bcm2835; then
        print_success "SPI is enabled and ready to use"
    else
        print_warning "IMPORTANT: A reboot is required to enable SPI interface"
        print_warning "Please reboot your Raspberry Pi with: sudo reboot"
    fi
    
    echo
    print_status "If you encounter any issues, check the troubleshooting section in README.md"
    print_status "Enjoy your new weather display system!"
}

# Main installation function
main() {
    echo
    print_status "=== Raspberry Pi Weather Display System - Setup Script ==="
    echo
    
    # Pre-installation checks
    check_root
    check_raspberry_pi
    
    # Installation steps
    update_system
    install_system_dependencies
    install_python_dependencies
    enable_spi
    create_project_directory
    copy_project_files
    install_font
    setup_systemd_service
    setup_api_key
    test_hardware
    start_service
    
    # Final instructions
    display_final_instructions
}

# Handle script interruption
trap 'print_error "Installation interrupted by user"; exit 1' INT

# Run main function
main "$@" 