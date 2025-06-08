import time
import requests
from PIL import Image, ImageDraw, ImageFont
import board
import digitalio
from adafruit_rgb_display import st7789
from datetime import datetime
from io import BytesIO
import logging

# Logging settings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SPI
spi = board.SPI()
cs_pin = digitalio.DigitalInOut(board.CE0)  # Chip Select
dc_pin = digitalio.DigitalInOut(board.D25)  # Data/Command
reset_pin = digitalio.DigitalInOut(board.D24)  # Reset

# ST7789
disp = st7789.ST7789(
    spi, cs=cs_pin, dc=dc_pin, rst=reset_pin, width=240, height=320, rotation=0
)

# Orbitron Bold fonts
font_path = "/usr/share/fonts/truetype/Orbitron-Bold.ttf"
try:
    font_large = ImageFont.truetype(font_path, 48)
    font_medium = ImageFont.truetype(font_path, 20)
    font_small = ImageFont.truetype(font_path, 19) 
    font_city_country = ImageFont.truetype(font_path, 14) 
    font_weather_temp = ImageFont.truetype(font_path, 16) 
    font_weekly = ImageFont.truetype(font_path, 12) 
except OSError:
    logger.error("Orbitron font could not be loaded.")
    # Use default font
    font_large = ImageFont.load_default()
    font_medium = ImageFont.load_default()
    font_small = ImageFont.load_default()
    font_city_country = ImageFont.load_default()
    font_weather_temp = ImageFont.load_default()
    font_weekly = ImageFont.load_default()

# API settings
WEATHER_API_KEY = "YOUR_API_KEY_HERE"  # Get your free API key from https://openweathermap.org/api
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_API_URL = "https://api.openweathermap.org/data/2.5/forecast"
LOCATION_API_URL = "http://ip-api.com/json"

# Validate API key
if WEATHER_API_KEY == "YOUR_API_KEY_HERE":
    logger.error("Please set your OpenWeatherMap API key in the WEATHER_API_KEY variable")
    logger.error("Get your free API key from: https://openweathermap.org/api")
    logger.error("Replace 'YOUR_API_KEY_HERE' with your actual API key")
    exit(1)

# Cache variables
last_weather_fetch = 0
cached_weather_data = None
last_location_fetch = 0
cached_location_data = None
CACHE_DURATION = 300  # 5 minutes

# Timeout settings
REQUEST_TIMEOUT = 10

def get_weather_and_location():
    global last_weather_fetch, cached_weather_data, last_location_fetch, cached_location_data
    current_time = time.time()
    
    try:
        # Location cache check
        if current_time - last_location_fetch > CACHE_DURATION or cached_location_data is None:
            logger.info("Fetching location data...")
            location_response = requests.get(LOCATION_API_URL, timeout=REQUEST_TIMEOUT)
            location_response.raise_for_status()
            cached_location_data = location_response.json()
            last_location_fetch = current_time
        
        city = cached_location_data.get("city", "Unknown").upper()
        country = cached_location_data.get("country", "Unknown").upper()
        country_code = cached_location_data.get("countryCode", "XX").upper()

        # Weather cache check
        if current_time - last_weather_fetch > CACHE_DURATION or cached_weather_data is None:
            logger.info("Fetching weather data...")
            weather_params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric"}
            weather_response = requests.get(WEATHER_API_URL, params=weather_params, timeout=REQUEST_TIMEOUT)
            weather_response.raise_for_status()
            cached_weather_data = weather_response.json()
            last_weather_fetch = current_time

        weather = cached_weather_data["weather"][0]["description"].upper()
        temperature = f"{cached_weather_data['main']['temp']:.1f}°C"
        icon_code = cached_weather_data["weather"][0]["icon"]

        return city, country, country_code, weather, temperature, icon_code
    
    except requests.exceptions.Timeout:
        logger.error("Request timeout")
        return "TIMEOUT", "ERROR", "XX", "CONNECTION ERROR", "N/A", None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {e}")
        return "NETWORK", "ERROR", "XX", "NETWORK ERROR", "N/A", None
    except KeyError as e:
        logger.error(f"API response error: {e}")
        return "API", "ERROR", "XX", "API ERROR", "N/A", None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "UNKNOWN", "ERROR", "XX", "UNKNOWN ERROR", "N/A", None

def fetch_country_flag(country_code):
    try:
        flag_url = f"https://flagcdn.com/w80/{country_code.lower()}.png" 
        response = requests.get(flag_url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            flag = Image.open(BytesIO(response.content)).convert("RGBA")
            return flag.resize((30, 20))
        else:
            logger.warning(f"Flag not found for country: {country_code}")
            return None
    except Exception as e:
        logger.error(f"Error fetching flag: {e}")
        return None

def fetch_weather_icon(icon_code, size=(50, 50)):
    try:
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
        response = requests.get(icon_url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            icon = Image.open(BytesIO(response.content)).convert("RGBA")
            return icon.resize(size) 
        else:
            logger.warning(f"Weather icon not found: {icon_code}")
            return None
    except Exception as e:
        logger.error(f"Error fetching icon: {e}")
        return None

def get_weekly_weather(city):
    try:
        forecast_params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric"}
        forecast_response = requests.get(FORECAST_API_URL, params=forecast_params, timeout=REQUEST_TIMEOUT)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        weekly_data = []
        # Check API data count
        forecast_list = forecast_data.get("list", [])
        
        for i in range(0, min(len(forecast_list), 40), 8):
            try:
                date = datetime.fromtimestamp(forecast_list[i]["dt"]).strftime("%a")
                temp = f"{int(forecast_list[i]['main']['temp'])}"  
                icon = forecast_list[i]["weather"][0]["icon"]
                weekly_data.append((date, temp, icon))
            except (KeyError, IndexError) as e:
                logger.warning(f"Weekly data processing error: {e}")
                continue

        return weekly_data[:7]
    except Exception as e:
        logger.error(f"Weekly forecast error: {e}")
        return []

def display_error_message(draw, error_msg):
    """Display error message on screen in case of error"""
    draw.rectangle((0, 0, 240, 320), fill="#100010")
    error_text = f"ERROR: {error_msg}"
    text_width = font_medium.getlength(error_text)
    text_x = (240 - text_width) // 2
    draw.text((text_x, 150), error_text, font=font_medium, fill="red")

# Main loop
error_count = 0
MAX_ERRORS = 3

logger.info("Weather Display starting...")

while True:
    try:
        # Create new image
        image = Image.new("RGB", (disp.width, disp.height))
        draw = ImageDraw.Draw(image)
        
        now = datetime.now()
        current_date = now.strftime("%d %B %Y").upper()
        current_day = now.strftime("%A").upper()
        current_time = now.strftime("%H:%M") 

        city, country, country_code, weather, temperature, icon_code = get_weather_and_location()
        
        # Error condition check
        if city in ["TIMEOUT", "NETWORK", "API", "UNKNOWN"]:
            display_error_message(draw, f"{city} - {weather}")
            disp.image(image)
            time.sleep(30)  # Wait shorter in case of error
            continue

        weekly_data = get_weekly_weather(city)

        # Background
        draw.rectangle((0, 0, 240, 320), fill="#100010")

        # Date
        date_width = font_small.getlength(current_date)
        date_x = (240 - date_width) // 2
        draw.text((date_x, 10), current_date, font=font_small, fill="white")

        # Day
        day_width = font_medium.getlength(current_day)
        day_x = (disp.width - day_width) // 2
        draw.text((day_x, 40), current_day, font=font_medium, fill="lime")

        # Clock
        time_width = font_large.getlength(current_time)
        time_x = (disp.width - time_width) // 2
        draw.text((time_x, 62), current_time, font=font_large, fill="cyan")

        # Line
        draw.line((10, 125, 230, 125), fill="white", width=2)

        # Location
        draw.text((10, 134), city, font=font_city_country, fill="yellow")
        draw.text((10, 159), country, font=font_city_country, fill="orange")  

        # Flag
        country_flag = fetch_country_flag(country_code)
        if country_flag:
            image.paste(country_flag, (200, 144), country_flag)

        # Line
        draw.line((10, 185, 230, 185), fill="white", width=2)
        
        # Weather info
        draw.text((10, 195), f"{weather}", font=font_weather_temp, fill="yellow")
        draw.text((10, 220), f"{temperature}", font=font_weather_temp, fill="orange")

        # Weather icon
        if icon_code:
            weather_icon = fetch_weather_icon(icon_code, size=(60, 60))
            if weather_icon:
                image.paste(weather_icon, (175, 200), weather_icon)

        # Line
        draw.line((10, 253, 230, 253), fill="white", width=2)

        # Weekly weather
        x_offset = 10 
        step = 46   
        for day, temp, icon in weekly_data:
            if x_offset + step > 240:  # Screen boundary check
                break
                
            draw.text((x_offset, 260), day, font=font_weekly, fill="white")
            draw.text((x_offset + 5, 275), temp, font=font_weekly, fill="cyan")
            
            icon_img = fetch_weather_icon(icon, size=(30, 30))  
            if icon_img:
                image.paste(icon_img, (x_offset, 290), icon_img)

            x_offset += step

        # Update screen
        disp.image(image)
        error_count = 0  # Reset error counter after successful update
        
        logger.info("Screen updated")
        time.sleep(60)

    except KeyboardInterrupt:
        logger.info("Program stopped by user")
        break
    except Exception as e:
        error_count += 1
        logger.error(f"Error in main loop #{error_count}: {e}")
        
        if error_count >= MAX_ERRORS:
            logger.critical("Too many errors, terminating program")
            break
            
        time.sleep(30)  # Wait short in case of error

logger.info("Program terminated")
