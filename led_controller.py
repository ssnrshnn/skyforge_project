import RPi.GPIO as GPIO
import time
import logging
import signal
import sys

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# GPIO Pins
LED1_PIN = 17  # First LED (Green) on GPIO 17 (Pin 11)
LED2_PIN = 27  # Second LED (Red) on GPIO 27 (Pin 13)

# GPIO settings
GPIO.setwarnings(False)  # Warnings are disabled to avoid "channel already in use" messages
GPIO.setmode(GPIO.BCM)   # Use BCM pin numbering

def setup_gpio():
    """Initialize GPIO pins"""
    try:
        GPIO.setup(LED1_PIN, GPIO.OUT)  # Configure LED1_PIN as output
        GPIO.setup(LED2_PIN, GPIO.OUT)  # Configure LED2_PIN as output
        # Ensure LEDs start in OFF state
        GPIO.output(LED1_PIN, GPIO.LOW)
        GPIO.output(LED2_PIN, GPIO.LOW)
        logger.info("GPIO pins initialized successfully")
    except Exception as e:
        logger.error(f"Error setting up GPIO: {e}")
        raise

def cleanup_gpio():
    """Clean up GPIO resources"""
    try:
        GPIO.output(LED1_PIN, GPIO.LOW)  # Turn off LED1
        GPIO.output(LED2_PIN, GPIO.LOW)  # Turn off LED2
        GPIO.cleanup()  # Reset all GPIO pins to a safe state
        logger.info("GPIO cleanup completed")
    except Exception as e:
        logger.error(f"Error during GPIO cleanup: {e}")

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    cleanup_gpio()
    sys.exit(0)

def blink_twice(pin, led_name="LED"):
    """Blink a specific LED twice quickly with error handling"""
    try:
        for i in range(2):
            GPIO.output(pin, GPIO.HIGH)  # Turn on the LED
            time.sleep(0.05)            # Wait for 50ms
            GPIO.output(pin, GPIO.LOW)  # Turn off the LED
            time.sleep(0.05)            # Wait for 50ms
    except Exception as e:
        logger.error(f"Error blinking {led_name}: {e}")

def main():
    """Main function with proper error handling"""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("LED Control starting...")
    
    try:
        setup_gpio()
        
        cycle_count = 0
        while True:
            cycle_count += 1
            
            # First LED (Green) blinks twice quickly
            blink_twice(LED1_PIN, "Green LED")
            
            # Wait 0.7 seconds
            time.sleep(0.7)
            
            # Second LED (Red) blinks twice quickly
            blink_twice(LED2_PIN, "Red LED")
            
            # Wait 1.2 seconds before the next cycle
            time.sleep(1.2)
            
            # Log every 50 cycles to avoid spam
            if cycle_count % 50 == 0:
                logger.info(f"LED cycle #{cycle_count} completed")
                
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
    finally:
        cleanup_gpio()
        logger.info("LED Control program terminated")

if __name__ == "__main__":
    main()
