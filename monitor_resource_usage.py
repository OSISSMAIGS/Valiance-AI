import psutil
import time
import os
import sys
import logging
import argparse
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("resource_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('resource_monitor')

def get_process_by_name(name):
    """Find a process by name"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        # Check if process name contains the given name
        if name.lower() in proc.info['name'].lower():
            return proc
        # Check if python is running our script
        elif proc.info['name'] == 'python' or proc.info['name'] == 'python3':
            cmdline = ' '.join(proc.info['cmdline'])
            if name in cmdline:
                return proc
    return None

def monitor_process(process, interval=5, duration=300, output_file=None):
    """Monitor a process's resource usage for a specified duration"""
    start_time = time.time()
    end_time = start_time + duration
    
    # Prepare data structure for metrics
    metrics = {
        'timestamp': [],
        'cpu_percent': [],
        'memory_percent': [],
        'memory_mb': [],
        'threads': [],
        'open_files': [],
        'connections': []
    }
    
    logger.info(f"Starting monitoring of process {process.pid} ({process.name()}) for {duration} seconds")
    
    try:
        while time.time() < end_time:
            current_time = time.time()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Get process metrics
            with process.oneshot():
                cpu_percent = process.cpu_percent(interval=0.1)
                memory_percent = process.memory_percent()
                memory_mb = process.memory_info().rss / (1024 * 1024)  # Convert to MB
                thread_count = len(process.threads())
                try:
                    open_files_count = len(process.open_files())
                except psutil.AccessDenied:
                    open_files_count = -1
                try:
                    connections_count = len(process.connections())
                except psutil.AccessDenied:
                    connections_count = -1
            
            # Log the metrics
            logger.info(f"[{timestamp}] CPU: {cpu_percent:.1f}%, Memory: {memory_mb:.2f}MB ({memory_percent:.1f}%), "
                        f"Threads: {thread_count}, Open Files: {open_files_count}, Connections: {connections_count}")
            
            # Store metrics
            metrics['timestamp'].append(timestamp)
            metrics['cpu_percent'].append(cpu_percent)
            metrics['memory_percent'].append(memory_percent)
            metrics['memory_mb'].append(memory_mb)
            metrics['threads'].append(thread_count)
            metrics['open_files'].append(open_files_count)
            metrics['connections'].append(connections_count)
            
            # Sleep until next interval
            elapsed = time.time() - current_time
            sleep_time = max(0, interval - elapsed)
            time.sleep(sleep_time)
            
    except psutil.NoSuchProcess:
        logger.error(f"Process {process.pid} no longer exists.")
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted.")
    except Exception as e:
        logger.error(f"Error during monitoring: {str(e)}")
    
    # Save metrics to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Metrics saved to {output_file}")
    
    # Calculate and display summary statistics
    if metrics['cpu_percent']:
        avg_cpu = sum(metrics['cpu_percent']) / len(metrics['cpu_percent'])
        max_cpu = max(metrics['cpu_percent'])
        avg_memory_mb = sum(metrics['memory_mb']) / len(metrics['memory_mb'])
        max_memory_mb = max(metrics['memory_mb'])
        
        logger.info("=== Summary Statistics ===")
        logger.info(f"Average CPU Usage: {avg_cpu:.1f}%")
        logger.info(f"Maximum CPU Usage: {max_cpu:.1f}%")
        logger.info(f"Average Memory Usage: {avg_memory_mb:.2f}MB")
        logger.info(f"Maximum Memory Usage: {max_memory_mb:.2f}MB")
        
        # Check if resource usage might be problematic
        if max_cpu > 90:
            logger.warning("High CPU usage detected! This could cause your application to be terminated.")
        if max_memory_mb > 512:  # Typical cPanel memory limit
            logger.warning("High memory usage detected! This could cause your application to be terminated (cPanel typically limits to 512MB).")

def monitor_system(interval=5, duration=300, output_file=None):
    """Monitor system-wide resource usage"""
    start_time = time.time()
    end_time = start_time + duration
    
    # Prepare data structure for metrics
    metrics = {
        'timestamp': [],
        'cpu_percent': [],
        'memory_percent': [],
        'memory_available_mb': [],
        'swap_percent': []
    }
    
    logger.info(f"Starting system monitoring for {duration} seconds")
    
    try:
        while time.time() < end_time:
            current_time = time.time()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Log the metrics
            logger.info(f"[{timestamp}] CPU: {cpu_percent:.1f}%, Memory: {memory.percent:.1f}%, "
                        f"Available Memory: {memory.available/(1024*1024):.2f}MB, Swap: {swap.percent:.1f}%")
            
            # Store metrics
            metrics['timestamp'].append(timestamp)
            metrics['cpu_percent'].append(cpu_percent)
            metrics['memory_percent'].append(memory.percent)
            metrics['memory_available_mb'].append(memory.available/(1024*1024))
            metrics['swap_percent'].append(swap.percent)
            
            # Sleep until next interval
            elapsed = time.time() - current_time
            sleep_time = max(0, interval - elapsed)
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted.")
    except Exception as e:
        logger.error(f"Error during monitoring: {str(e)}")
    
    # Save metrics to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Metrics saved to {output_file}")
    
    # Calculate and display summary statistics
    if metrics['cpu_percent']:
        avg_cpu = sum(metrics['cpu_percent']) / len(metrics['cpu_percent'])
        max_cpu = max(metrics['cpu_percent'])
        avg_memory = sum(metrics['memory_percent']) / len(metrics['memory_percent'])
        max_memory = max(metrics['memory_percent'])
        min_available_mb = min(metrics['memory_available_mb'])
        
        logger.info("=== Summary Statistics ===")
        logger.info(f"Average CPU Usage: {avg_cpu:.1f}%")
        logger.info(f"Maximum CPU Usage: {max_cpu:.1f}%")
        logger.info(f"Average Memory Usage: {avg_memory:.1f}%")
        logger.info(f"Maximum Memory Usage: {max_memory:.1f}%")
        logger.info(f"Minimum Available Memory: {min_available_mb:.2f}MB")
        
        # Check if resource usage might be problematic
        if min_available_mb < 100:
            logger.warning("Low available memory detected! This could cause applications to be terminated.")

def main():
    parser = argparse.ArgumentParser(description="Monitor resource usage of a process or the entire system")
    parser.add_argument("--process", help="Name of the process to monitor (e.g., 'python', 'main.py')")
    parser.add_argument("--interval", type=int, default=5, help="Monitoring interval in seconds")
    parser.add_argument("--duration", type=int, default=300, help="Total monitoring duration in seconds")
    parser.add_argument("--output", help="Output file for saving metrics as JSON")
    args = parser.parse_args()
    
    if args.process:
        process = get_process_by_name(args.process)
        if process:
            monitor_process(process, args.interval, args.duration, args.output)
        else:
            logger.error(f"No process found matching '{args.process}'")
            sys.exit(1)
    else:
        monitor_system(args.interval, args.duration, args.output)

if __name__ == "__main__":
    main() 