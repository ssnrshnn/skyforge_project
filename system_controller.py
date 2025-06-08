import multiprocessing
import subprocess
import signal
import sys
import time
import logging
from pathlib import Path

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables for process management
process_a = None
process_b = None
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True
    
    # Terminate child processes
    terminate_processes()
    sys.exit(0)

def terminate_processes():
    """Terminate all child processes gracefully"""
    global process_a, process_b
    
    if process_a and process_a.is_alive():
        logger.info("Terminating weather display process...")
        process_a.terminate()
        process_a.join(timeout=5)  # Wait up to 5 seconds
        if process_a.is_alive():
            logger.warning("Force killing weather display process...")
            process_a.kill()
    
    if process_b and process_b.is_alive():
        logger.info("Terminating LED control process...")
        process_b.terminate()
        process_b.join(timeout=5)  # Wait up to 5 seconds
        if process_b.is_alive():
            logger.warning("Force killing LED control process...")
            process_b.kill()

def run_script_with_restart(script_name, max_restarts=5):
    """Run a script with automatic restart capability"""
    restart_count = 0
    
    while not shutdown_requested and restart_count < max_restarts:
        try:
            logger.info(f"Starting {script_name} (attempt {restart_count + 1})")
            result = subprocess.run(
                ["python3", script_name], 
                check=False,  # Don't raise exception on non-zero exit
                capture_output=False,  # Allow real-time output
                timeout=None  # No timeout
            )
            
            if result.returncode != 0:
                logger.error(f"{script_name} exited with code {result.returncode}")
            else:
                logger.info(f"{script_name} completed normally")
                
        except subprocess.TimeoutExpired:
            logger.error(f"{script_name} timed out")
        except Exception as e:
            logger.error(f"Error running {script_name}: {e}")
        
        restart_count += 1
        
        if not shutdown_requested and restart_count < max_restarts:
            wait_time = min(30, restart_count * 5)  # Progressive backoff
            logger.info(f"Restarting {script_name} in {wait_time} seconds...")
            time.sleep(wait_time)
    
    if restart_count >= max_restarts:
        logger.critical(f"{script_name} failed {max_restarts} times, giving up")

def run_weather_display():
    """Run weather display script with restart capability"""
    run_script_with_restart("weather_display.py")

def run_led_controller():
    """Run LED control script with restart capability"""
    run_script_with_restart("led_controller.py")

def check_script_files():
    """Check if required script files exist"""
    scripts = ["weather_display.py", "led_controller.py"]
    missing_scripts = []
    
    for script in scripts:
        if not Path(script).exists():
            missing_scripts.append(script)
    
    if missing_scripts:
        logger.error(f"Missing script files: {missing_scripts}")
        return False
    
    logger.info("All required script files found")
    return True

def monitor_processes():
    """Monitor child processes and restart if needed"""
    global process_a, process_b
    
    while not shutdown_requested:
        try:
            # Check process A (weather display)
            if process_a and not process_a.is_alive():
                exit_code = process_a.exitcode
                logger.warning(f"Weather display process died (exit code: {exit_code})")
                process_a = multiprocessing.Process(target=run_weather_display)
                process_a.start()
                logger.info("Weather display process restarted")
            
            # Check process B (LED control)
            if process_b and not process_b.is_alive():
                exit_code = process_b.exitcode
                logger.warning(f"LED control process died (exit code: {exit_code})")
                process_b = multiprocessing.Process(target=run_led_controller)
                process_b.start()
                logger.info("LED control process restarted")
            
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            logger.error(f"Error in process monitoring: {e}")
            time.sleep(5)

def main():
    """Main function with comprehensive error handling"""
    global process_a, process_b
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("System Controller starting...")
    
    # Check if required files exist
    if not check_script_files():
        logger.critical("Cannot start - missing required files")
        sys.exit(1)
    
    try:
        # Start both processes
        logger.info("Starting weather display process...")
        process_a = multiprocessing.Process(target=run_weather_display, name="WeatherDisplay")
        
        logger.info("Starting LED control process...")
        process_b = multiprocessing.Process(target=run_led_controller, name="LEDController")
        
        process_a.start()
        process_b.start()
        
        logger.info("Both processes started successfully")
        
        # Monitor processes
        monitor_processes()
        
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
    finally:
        terminate_processes()
        logger.info("System Controller terminated")

if __name__ == "__main__":
    main()
