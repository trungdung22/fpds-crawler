#!/usr/bin/env python3
"""
FPDS Crawler Service Manager
Manages the systemd service with parameter parsing and monitoring
"""
import argparse
import subprocess
import sys
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import calendar

class FPDSServiceManager:
    """Manages the FPDS crawler systemd service"""
    
    def __init__(self):
        self.service_name = "fpds-crawler"
        self.service_file = f"/etc/systemd/system/{self.service_name}.service"
        self.log_file = "/var/log/fpds-crawler.log"
        self.error_log_file = "/var/log/fpds-crawler.error.log"
        self.config_file = "/etc/fpds-crawler/config.json"
    
    def parse_month_year(self, month_year_str: str) -> tuple:
        """Parse month/year format (e.g., '1/2026') and return start/end dates for the month"""
        try:
            # Parse month/year format
            if '/' in month_year_str:
                month, year = month_year_str.split('/')
                month = int(month)
                year = int(year)
            else:
                raise ValueError("Invalid format. Use M/YYYY (e.g., 1/2026)")
            
            # Validate month and year
            if month < 1 or month > 12:
                raise ValueError("Month must be between 1 and 12")
            if year < 1900 or year > 2100:
                raise ValueError("Year must be between 1900 and 2100")
            
            # Get first and last day of the month
            first_day = datetime(year, month, 1)
            last_day = datetime(year, month, calendar.monthrange(year, month)[1])
            
            # Format as YYYY/MM/DD
            start_date = first_day.strftime('%Y/%m/%d')
            end_date = last_day.strftime('%Y/%m/%d')
            
            return start_date, end_date
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid month/year format: {month_year_str}. Use M/YYYY (e.g., 1/2026)") from e
        
    def create_service_file(self, params: dict):
        """Create systemd service file with parameters"""
        
        # Build command line arguments
        cmd_args = [
            "/usr/bin/python3",
            "fpds_high_performance.py"
        ]
        
        # Add parameters
        if params.get('target_records'):
            cmd_args.extend(['--target-records', str(params['target_records'])])
        if params.get('workers'):
            cmd_args.extend(['--workers', str(params['workers'])])
        if params.get('batch_size'):
            cmd_args.extend(['--batch-size', str(params['batch_size'])])
        if params.get('start_date'):
            cmd_args.extend(['--start-date', params['start_date']])
        if params.get('end_date'):
            cmd_args.extend(['--end-date', params['end_date']])
        if params.get('initial_delay'):
            cmd_args.extend(['--initial-delay', str(params['initial_delay'])])
        if params.get('agency'):
            cmd_args.extend(['--agency', params['agency']])
        if params.get('vendor'):
            cmd_args.extend(['--vendor', params['vendor']])
        if params.get('enable_retry'):
            cmd_args.append('--enable-retry')
        if params.get('max_retries'):
            cmd_args.extend(['--max-retries', str(params['max_retries'])])
        
        exec_start = ' '.join(cmd_args)
        
        # Service file template
        service_content = f"""[Unit]
Description=FPDS High Performance Crawler Service
After=network.target
Wants=network.target
Documentation=https://github.com/trungdung22/fpds-crawler

[Service]
Type=simple
User=fpds-crawler
Group=fpds-crawler
WorkingDirectory=/home/fpds-crawler/fpds-crawler
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=/home/fpds-crawler/fpds-crawler
ExecStart={exec_start}
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=fpds-crawler

# Resource limits
MemoryMax=8G
CPUQuota=400%
LimitNOFILE=65536

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/fpds-crawler/fpds-crawler/result_data,/home/fpds-crawler/fpds-crawler/failed_request_data

# Logging
StandardOutput=append:{self.log_file}
StandardError=append:{self.error_log_file}

[Install]
WantedBy=multi-user.target
"""
        
        # Write service file
        try:
            with open(self.service_file, 'w') as f:
                f.write(service_content)
            print(f"Service file created: {self.service_file}")
            print(f"Command: {exec_start}")
            
            # Save configuration
            self.save_config(params)
            
        except PermissionError:
            print("Error: Need sudo privileges to create service file")
            sys.exit(1)
    
    def save_config(self, params: dict):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(params, f, indent=2)
        print(f"Configuration saved: {self.config_file}")
    
    def load_config(self) -> dict:
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def run_command(self, cmd: list, check=True) -> subprocess.CompletedProcess:
        """Run system command"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)
            return result
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {' '.join(cmd)}")
            print(f"Error: {e.stderr}")
            if check:
                sys.exit(1)
            return e
    
    def start_service(self):
        """Start the FPDS crawler service"""
        print("Starting FPDS crawler service...")
        
        # Reload systemd
        self.run_command(['systemctl', 'daemon-reload'])
        
        # Start service
        result = self.run_command(['systemctl', 'start', self.service_name], check=False)
        if result.returncode == 0:
            print("Service started successfully")
        else:
            print("Failed to start service")
            print(f"Error: {result.stderr}")
    
    def stop_service(self):
        """Stop the FPDS crawler service"""
        print("Stopping FPDS crawler service...")
        result = self.run_command(['systemctl', 'stop', self.service_name], check=False)
        if result.returncode == 0:
            print("Service stopped successfully")
        else:
            print("Failed to stop service")
    
    def restart_service(self):
        """Restart the FPDS crawler service"""
        print("Restarting FPDS crawler service...")
        result = self.run_command(['systemctl', 'restart', self.service_name], check=False)
        if result.returncode == 0:
            print("Service restarted successfully")
        else:
            print("Failed to restart service")
    
    def get_status(self):
        """Get service status"""
        result = self.run_command(['systemctl', 'status', self.service_name], check=False)
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"Service status error: {result.stderr}")
    
    def get_logs(self, lines: int = 1000, follow: bool = False):
        """Get service logs"""
        cmd = ['journalctl', '-u', self.service_name, '-n', str(lines)]
        if follow:
            cmd.append('-f')
        
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            if follow:
                print("\nStopped following logs")
    
    def get_file_logs(self, lines: int = 1000):
        """Get logs from log files"""
        if os.path.exists(self.log_file):
            print(f"\n=== Main Log ({self.log_file}) ===")
            try:
                result = subprocess.run(['tail', '-n', str(lines), self.log_file], 
                                      capture_output=True, text=True)
                print(result.stdout)
            except Exception as e:
                print(f"Error reading log file: {e}")
        
        if os.path.exists(self.error_log_file):
            print(f"\n=== Error Log ({self.error_log_file}) ===")
            try:
                result = subprocess.run(['tail', '-n', str(lines), self.error_log_file], 
                                      capture_output=True, text=True)
                print(result.stdout)
            except Exception as e:
                print(f"Error reading error log file: {e}")
    
    def enable_service(self):
        """Enable service to start on boot"""
        print("Enabling FPDS crawler service...")
        result = self.run_command(['systemctl', 'enable', self.service_name], check=False)
        if result.returncode == 0:
            print("Service enabled successfully")
        else:
            print("Failed to enable service")
    
    def disable_service(self):
        """Disable service from starting on boot"""
        print("Disabling FPDS crawler service...")
        result = self.run_command(['systemctl', 'disable', self.service_name], check=False)
        if result.returncode == 0:
            print("Service disabled successfully")
        else:
            print("Failed to disable service")
    
    def show_config(self):
        """Show current configuration"""
        config = self.load_config()
        if config:
            print("Current Configuration:")
            for key, value in config.items():
                print(f"  {key}: {value}")
        else:
            print("No configuration found")
    
    def show_metrics(self):
        """Show service metrics"""
        print("=== FPDS Crawler Service Metrics ===")
        
        # Service status
        status_result = self.run_command(['systemctl', 'is-active', self.service_name], check=False)
        print(f"Service Status: {status_result.stdout.strip()}")
        
        # Uptime
        uptime_result = self.run_command(['systemctl', 'show', self.service_name, '--property=ActiveEnterTimestamp'], check=False)
        if uptime_result.returncode == 0:
            timestamp = uptime_result.stdout.strip().split('=')[1]
            print(f"Started: {timestamp}")
        
        # Memory usage
        try:
            memory_result = subprocess.run(['systemctl', 'show', self.service_name, '--property=MemoryCurrent'], 
                                         capture_output=True, text=True, check=False)
            if memory_result.returncode == 0:
                memory = memory_result.stdout.strip().split('=')[1]
                if memory != 'infinity':
                    memory_mb = int(memory) / (1024 * 1024)
                    print(f"Memory Usage: {memory_mb:.1f} MB")
        except:
            pass
        
        # Log file sizes
        if os.path.exists(self.log_file):
            size = os.path.getsize(self.log_file) / (1024 * 1024)
            print(f"Log File Size: {size:.1f} MB")
        
        if os.path.exists(self.error_log_file):
            size = os.path.getsize(self.error_log_file) / (1024 * 1024)
            print(f"Error Log Size: {size:.1f} MB")

def main():
    parser = argparse.ArgumentParser(description='FPDS Crawler Service Manager')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Install service with parameters')
    install_parser.add_argument('--target-records', type=int, default=2000000, help='Target records to extract')
    install_parser.add_argument('--workers', type=int, default=16, help='Number of worker threads')
    install_parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing')
    install_parser.add_argument('--month-year', default='1/2026', help='Month/Year to process (M/YYYY format, e.g., 1/2026)')
    install_parser.add_argument('--initial-delay', type=float, default=0.5, help='Initial delay between requests')
    install_parser.add_argument('--agency', help='Filter by agency name')
    install_parser.add_argument('--vendor', help='Filter by vendor name')
    install_parser.add_argument('--enable-retry', action='store_true', default=True, help='Enable automatic retry (default: True)')
    install_parser.add_argument('--max-retries', type=int, default=3, help='Maximum retry attempts')
    
    # Service control commands
    subparsers.add_parser('start', help='Start the service')
    subparsers.add_parser('stop', help='Stop the service')
    subparsers.add_parser('restart', help='Restart the service')
    subparsers.add_parser('status', help='Show service status')
    subparsers.add_parser('enable', help='Enable service on boot')
    subparsers.add_parser('disable', help='Disable service on boot')
    
    # Logging commands
    logs_parser = subparsers.add_parser('logs', help='Show service logs')
    logs_parser.add_argument('-n', '--lines', type=int, default=1000, help='Number of lines to show')
    logs_parser.add_argument('-f', '--follow', action='store_true', help='Follow logs in real-time')
    
    file_logs_parser = subparsers.add_parser('file-logs', help='Show log files')
    file_logs_parser.add_argument('-n', '--lines', type=int, default=1000, help='Number of lines to show')
    
    # Info commands
    subparsers.add_parser('config', help='Show current configuration')
    subparsers.add_parser('metrics', help='Show service metrics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = FPDSServiceManager()
    
    if args.command == 'install':
        # Parse month/year and convert to start/end dates
        try:
            start_date, end_date = manager.parse_month_year(args.month_year)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        
        # Convert args to dict
        params = {
            'target_records': args.target_records,
            'workers': args.workers,
            'batch_size': args.batch_size,
            'start_date': start_date,
            'end_date': end_date,
            'initial_delay': args.initial_delay,
            'agency': args.agency,
            'vendor': args.vendor,
            'enable_retry': args.enable_retry,
            'max_retries': args.max_retries
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        manager.create_service_file(params)
        manager.enable_service()
        print("\nService installed successfully!")
        print(f"Processing period: {start_date} to {end_date}")
        print("Use 'sudo fpds-crawler-manager.py start' to start the service")
        
    elif args.command == 'start':
        manager.start_service()
    elif args.command == 'stop':
        manager.stop_service()
    elif args.command == 'restart':
        manager.restart_service()
    elif args.command == 'status':
        manager.get_status()
    elif args.command == 'enable':
        manager.enable_service()
    elif args.command == 'disable':
        manager.disable_service()
    elif args.command == 'logs':
        manager.get_logs(args.lines, args.follow)
    elif args.command == 'file-logs':
        manager.get_file_logs(args.lines)
    elif args.command == 'config':
        manager.show_config()
    elif args.command == 'metrics':
        manager.show_metrics()

if __name__ == "__main__":
    main() 