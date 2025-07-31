# FPDS Crawler VM Deployment Guide

This guide explains how to deploy the FPDS crawler on a Google Cloud VM using Ubuntu's default Python3.

## Prerequisites

1. **Google Cloud SDK** installed and configured
2. **gcloud** authenticated with appropriate permissions
3. **Project ID** set to `cloudmatos-saas-demo`

## Quick Deployment

### 1. Create VM with Auto-Setup

```bash
# Make scripts executable
chmod +x script/*.sh

# Create VM (this will automatically install everything)
./script/create_vm.sh
```

The script will:
- Create a VM with Ubuntu 24.02 LTS
- Install Python3 and all required packages
- Clone the FPDS crawler repository
- Set up the service environment
- Create necessary directories and permissions

### 2. Connect to VM

After the VM is created, connect via gcloud compute ssh:

```bash
gcloud compute ssh fpds-crawler-vm --zone=us-central1-a --project=cloudmatos-saas-demo
```

### 3. Verify Setup

```bash
# Test the installation
python3 test_setup.py

# Check the crawler manager
sudo python3 fpds-crawler-manager.py --help
```

### 4. Start the Service

```bash
# Install and start the service
sudo python3 fpds-crawler-manager.py install --target-records 10000 --workers 8
sudo python3 fpds-crawler-manager.py start

# Check status
sudo python3 fpds-crawler-manager.py status
```

## VM Configuration

### Machine Specifications
- **Type**: e2-standard-4 (4 vCPUs, 16 GB memory)
- **Disk**: 200GB standard persistent disk
- **OS**: Ubuntu 22.04 LTS
- **Zone**: asia-southeast1-a

### Installed Components
- Python3 and pip3
- Required Python packages (see requirements.txt)
- Git for repository cloning
- System dependencies for web scraping

## Service Management

### Available Commands

```bash
# Service control
sudo python3 fpds-crawler-manager.py start
sudo python3 fpds-crawler-manager.py stop
sudo python3 fpds-crawler-manager.py restart
sudo python3 fpds-crawler-manager.py status

# Logging
sudo python3 fpds-crawler-manager.py logs
sudo python3 fpds-crawler-manager.py logs -f  # Follow logs
sudo python3 fpds-crawler-manager.py file-logs

# Configuration
sudo python3 fpds-crawler-manager.py config
sudo python3 fpds-crawler-manager.py metrics

# Service lifecycle
sudo python3 fpds-crawler-manager.py enable   # Start on boot
sudo python3 fpds-crawler-manager.py disable  # Don't start on boot
```

### Installation with Parameters

```bash
sudo python3 fpds-crawler-manager.py install \
    --target-records 50000 \
    --workers 16 \
    --batch-size 100 \
    --start-date "2025/07/29" \
    --end-date "2025/07/30" \
    --initial-delay 0.5 \
    --enable-retry \
    --max-retries 3
```

## Direct Script Usage

You can also run the crawler directly without the service:

```bash
cd /home/fpds-crawler/fpds-crawler
python3 fpds_high_performance.py \
    --target-records 10000 \
    --workers 8 \
    --start-date "2025/07/29" \
    --end-date "2025/07/30"
```

### Remote Commands

You can run commands on the VM without SSHing in:

```bash
# Check service status
gcloud compute ssh fpds-crawler-vm --zone=us-central1-a --project=cloudmatos-saas-demo --command='sudo python3 fpds-crawler-manager.py status'

# View recent logs
gcloud compute ssh fpds-crawler-vm --zone=us-central1-a --project=cloudmatos-saas-demo --command='sudo python3 fpds-crawler-manager.py logs -n 20'

# Check system resources
gcloud compute ssh fpds-crawler-vm --zone=us-central1-a --project=cloudmatos-saas-demo --command='free -h && df -h'
```

## Monitoring and Logs

### Service Logs
- **System logs**: `sudo journalctl -u fpds-crawler -f`
- **Application logs**: `/var/log/fpds-crawler.log`
- **Error logs**: `/var/log/fpds-crawler.error.log`

### Resource Monitoring
```bash
# Service metrics
sudo python3 fpds-crawler-manager.py metrics

# System resources
htop
df -h
free -h
```

## Data Output

### Output Locations
- **Extracted data**: `/home/fpds-crawler/fpds-crawler/result_data/`
- **Failed requests**: `/home/fpds-crawler/fpds-crawler/failed_request_data/`
- **Configuration**: `/etc/fpds-crawler/config.json`

### File Formats
- **Results**: JSON files with timestamp (e.g., `fpds_high_performance_20250731_122707.json`)
- **Failed requests**: JSON files for retry processing

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo python3 fpds-crawler-manager.py status
   sudo journalctl -u fpds-crawler -n 50
   ```

2. **Permission issues**
   ```bash
   sudo chown -R fpds-crawler:fpds-crawler /home/fpds-crawler/
   sudo chmod +x /home/fpds-crawler/fpds-crawler/*.py
   ```

3. **Python package issues**
   ```bash
   sudo -u fpds-crawler python3 -m pip install --upgrade -r requirements.txt
   ```

4. **Network connectivity**
   ```bash
   python3 test_setup.py
   curl -I https://www.fpds.gov
   ```

### Retry Failed Requests

```bash
# Retry all failed requests
python3 fpds_high_performance.py --retry-failed --max-retries 3
```

## Cleanup

### Delete VM and Resources

```bash
./script/delete_vm.sh
```

This will:
- Delete the VM instance
- Remove firewall rules
- Clean up all associated resources

### Manual Cleanup

```bash
# Stop and disable service
sudo python3 fpds-crawler-manager.py stop
sudo python3 fpds-crawler-manager.py disable

# Remove service files
sudo rm -f /etc/systemd/system/fpds-crawler.service
sudo systemctl daemon-reload

# Remove user and data
sudo userdel -r fpds-crawler
sudo rm -rf /etc/fpds-crawler
sudo rm -f /var/log/fpds-crawler*.log
```

## Security Considerations

- The service runs as a dedicated `fpds-crawler` user
- Limited file system access with `ProtectSystem=strict`
- No new privileges allowed
- Private temporary directories
- Resource limits configured

## Performance Tuning

### Recommended Settings by Use Case

**Small dataset (1K-10K records):**
```bash
--workers 4 --batch-size 50 --initial-delay 1.0
```

**Medium dataset (10K-100K records):**
```bash
--workers 8 --batch-size 100 --initial-delay 0.5
```

**Large dataset (100K+ records):**
```bash
--workers 16 --batch-size 100 --initial-delay 0.3
```

### Resource Monitoring
- Monitor memory usage: `free -h`
- Monitor CPU usage: `htop`
- Monitor disk usage: `df -h`
- Monitor network: `iftop`

## Support

For issues or questions:
1. Check the logs first
2. Run the test script: `python3 test_setup.py`
3. Verify network connectivity
4. Check service status and configuration 