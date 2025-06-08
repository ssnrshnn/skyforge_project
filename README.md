# Raspberry Pi Weather Display System

A comprehensive weather display system for Raspberry Pi featuring a ST7789 TFT display and LED status indicators. The system shows current weather, time, date, location information, and 7-day weather forecast with automatic location detection.

## Quick Start (Automated Installation)

For the easiest installation experience, use the automated setup script:

```bash
# Download all project files to your Raspberry Pi
# Make the setup script executable
chmod +x setup.sh

# Run the automated setup
./setup.sh
```

The setup script will automatically:
- Update your system packages
- Install all required dependencies
- Enable SPI interface
- Configure the systemd service
- Set up fonts and project files
- Test hardware connections (optional)
- Start the weather display service

**That's it!** Your weather display system will be up and running.

---

## Manual Installation

If you prefer to install manually or want to understand each step, follow the detailed instructions below.

## Features

- **Real-time Weather Display**: Current weather conditions with temperature and weather icons
- **Automatic Location Detection**: Uses IP-based geolocation to detect your location
- **5-Day Weather Forecast**: Weekly weather preview with temperatures and icons
- **Time & Date Display**: Current time and date with custom Orbitron font
- **Country Flag Display**: Shows your country's flag next to location information
- **LED Status Indicators**: Visual status indicators with customizable patterns
- **Robust Error Handling**: Automatic restart and error recovery mechanisms
- **Systemd Service**: Runs as a system service for automatic startup

## Hardware Requirements

### Components
- Raspberry Pi (3B+ or newer recommended)
- ST7789 TFT Display (240x320 pixels)
- 2x LEDs (Green and Red)
- 2x 220Ω Resistors
- Jumper wires
- Breadboard (optional)

### Pin Connections

#### ST7789 Display Connections
| Display Pins | Raspberry Pi Pins                      |
| ------------ | -------------------------------------- |
| VCC          | 3.3V (Pin 1 or Pin 17)                 |
| GND          | GND (Pin 6, 9, 14, 20, 25, 30, 34, 39) |
| CS           | GPIO 8 (Pin 24 - SPI0_CE0)             |
| DC           | GPIO 25 (Pin 22)                       |
| RST          | GPIO 24 (Pin 18)                       |
| SDA          | GPIO 10 (Pin 19 - SPI0_MOSI)           |
| SCL          | GPIO 11 (Pin 23 - SPI0_SCLK)           |

#### LED Connections

**Green LED (Status Indicator):**
- Long leg (Anode) → 220Ω Resistor → GPIO 17 (Pin 11)
- Short leg (Cathode) → GND (any available GND pin)

**Red LED (Status Indicator):**
- Long leg (Anode) → 220Ω Resistor → GPIO 27 (Pin 13)
- Short leg (Cathode) → GND (any available GND pin)

## Software Requirements

### System Dependencies
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install python3 python3-pip git -y
```

### Python Dependencies
```bash
pip3 install requests pillow adafruit-circuitpython-rgb-display RPi.GPIO
```

### Enable SPI Interface
```bash
sudo raspi-config
# Navigate to: Interfacing Options → SPI → Enable
# Reboot after enabling
sudo reboot
```

## Installation

1. **Clone or download the project files to your Raspberry Pi:**
   ```bash
   cd /home/pi
   # Copy all project files (main.py, a.py, b.py, Orbitron-Bold.ttf, weather-display.service)
   ```

2. **Install the Orbitron font:**
   ```bash
   sudo mkdir -p /usr/share/fonts/truetype/
   sudo cp Orbitron-Bold.ttf /usr/share/fonts/truetype/
   sudo fc-cache -fv
   ```

3. **Set up the systemd service:**
   ```bash
   sudo cp weather-display.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable weather-display.service
   ```

4. **Start the service:**
   ```bash
   sudo systemctl start weather-display.service
   ```

## Configuration

### Weather API Setup
This project requires a free OpenWeatherMap API key to function properly.

1. **Get your free API key:**
   - Visit [OpenWeatherMap API](https://openweathermap.org/api)
   - Sign up for a free account
   - Generate your API key (free tier allows 1000 calls/day)

2. **Configure the API key:**
   - If using the automated setup script, you'll be prompted to enter your API key
   - For manual setup, replace `YOUR_API_KEY_HERE` in `a.py`:
   ```python
   WEATHER_API_KEY = "your_actual_api_key_here"
   ```

**Note:** The weather display will not work without a valid API key.

### Customization Options

#### Display Settings (a.py)
- **Update Interval**: Modify `time.sleep(60)` to change refresh rate
- **Font Sizes**: Adjust font size variables for different text elements
- **Colors**: Change color values in the drawing functions
- **Cache Duration**: Modify `CACHE_DURATION` for API call frequency

#### LED Patterns (b.py)
- **Blink Timing**: Adjust `time.sleep()` values in the main loop
- **LED Pins**: Change `LED1_PIN` and `LED2_PIN` for different GPIO pins
- **Blink Pattern**: Modify the `blink_twice()` function for custom patterns

## File Structure

```
├── main.py                 # Main controller with process management
├── a.py                    # Weather display functionality
├── b.py                    # LED control functionality
├── Orbitron-Bold.ttf       # Custom font file
├── weather-display.service # Systemd service configuration
├── setup.sh               # Automated installation script
├── .gitignore             # Git ignore file for security
└── README.md              # This file
```

## Usage

### Manual Operation
```bash
# Run the complete system
python3 main.py

# Run only weather display
python3 a.py

# Run only LED control
python3 b.py
```

### Service Management
```bash
# Check service status
sudo systemctl status weather-display.service

# Stop the service
sudo systemctl stop weather-display.service

# Restart the service
sudo systemctl restart weather-display.service

# View logs
sudo journalctl -u weather-display.service -f
```

## Troubleshooting

### Common Issues

1. **Display not working:**
   - Check SPI is enabled: `lsmod | grep spi`
   - Verify wiring connections
   - Check power supply (3.3V, not 5V)

2. **LEDs not blinking:**
   - Verify GPIO pin connections
   - Check resistor values (220Ω)
   - Ensure proper LED polarity

3. **Weather data not loading:**
   - Check internet connection
   - Verify API key validity
   - Check firewall settings

4. **Font not loading:**
   - Ensure font file is in `/usr/share/fonts/truetype/`
   - Run `sudo fc-cache -fv` to refresh font cache

### Log Files
- System logs: `sudo journalctl -u weather-display.service`
- Application logs are printed to console with timestamps

## API Usage

The system uses the following APIs:
- **OpenWeatherMap**: Current weather and 5-day forecast
- **IP-API**: Automatic location detection
- **FlagCDN**: Country flag images

## Performance

- **Memory Usage**: ~50-100MB RAM
- **CPU Usage**: <5% on Raspberry Pi 4
- **Network Usage**: ~1MB per hour (with caching)
- **Update Frequency**: Weather data every 5 minutes, display every 60 seconds

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## Security Notes

- **Never commit API keys** to version control
- **Keep your API key private** - don't share it publicly
- **Use environment variables** for production deployments
- **Regularly rotate your API keys** for better security
- The included `.gitignore` file helps prevent accidental commits of sensitive files

## License

This project is open source. Please respect the terms of service of the APIs used.

## Acknowledgments

- OpenWeatherMap for weather data API
- Adafruit for the display libraries
- FlagCDN for country flag images
- Google Fonts for the Orbitron font family 