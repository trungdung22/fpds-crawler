# FPDS Crawler Service Deployment Guide

This guide shows how to deploy the FPDS crawler as a systemd service on Ubuntu with full parameter control and monitoring capabilities.

## 🚀 Quick Start

### 1. Deploy on GCP VM (Recommended)

```bash
# Create GCP VM with 2 CPU, 8 GB RAM
gcloud compute instances create fpds-crawler \
  --zone=us-central1-a \
  --machine-type=e2-standard-2 \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-standard \
  --tags=http-server,https-server

# SSH to VM
gcloud compute ssh fpds-crawler --zone=us-central1-a
```

### 2. Run Setup Script

```bash
# Upload your crawler code to VM
# Then run setup script
sudo bash setup_fpds_service.sh
```

### 3. Install Service with Parameters

```bash
# Install service with your parameters
sudo fpds-crawler-manager.py install \
  --target-records 20000 \
  --workers 16 \
  --batch-size 100 \
  --start-date 2025/07/29 \
  --end-date 2025/07/30 \
  --enable-retry
```

### 4. Start and Monitor

```bash
# Start the service
sudo fpds-crawler-manager.py start

# Check status
sudo fpds-crawler-manager.py status

# View last 1000 log lines
sudo fpds-crawler-manager.py logs -n 1000

# Monitor in real-time
sudo fpds-crawler-manager.py logs -f
```

## 📋 Complete Usage Guide

### Service Management Commands

```bash
# Install service with parameters
sudo fpds-crawler-manager.py install [OPTIONS]

# Service control
sudo fpds-crawler-manager.py start
sudo fpds-crawler-manager.py stop
sudo fpds-crawler-manager.py restart

# Service status and monitoring
sudo fpds-crawler-manager.py status
sudo fpds-crawler-manager.py metrics
sudo fpds-crawler-manager.py config

# Logging
sudo fpds-crawler-manager.py logs [-n 1000] [-f]
sudo fpds-crawler-manager.py file-logs [-n 1000]

# Boot control
sudo fpds-crawler-manager.py enable
sudo fpds-crawler-manager.py disable
```

### Available Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--target-records` | 20000 | Target number of records to extract |
| `--workers` | 16 | Number of worker threads |
| `--batch-size` | 100 | Batch size for processing |
| `--start-date` | 2025/07/29 | Start date (YYYY/MM/DD) |
| `--end-date` | 2025/07/30 | End date (YYYY/MM/DD) |
| `--initial-delay` | 0.5 | Initial delay between requests |
| `--agency` | None | Filter by agency name |
| `--vendor` | None | Filter by vendor name |
| `--enable-retry` | False | Enable automatic retry |
| `--max-retries` | 3 | Maximum retry attempts |

### Example Configurations

#### Basic Daily Crawling
```bash
sudo fpds-crawler-manager.py install \
  --target-records 20000 \
  --workers 16 \
  --batch-size 100 \
  --start-date 2025/07/29 \
  --end-date 2025/07/30
```

#### Agency-Specific Crawling
```bash
sudo fpds-crawler-manager.py install \
  --target-records 50000 \
  --workers 8 \
  --batch-size 50 \
  --agency "NASA" \
  --start-date 2025/07/01 \
  --end-date 2025/07/31 \
  --enable-retry
```

#### High-Performance Crawling
```bash
sudo fpds-crawler-manager.py install \
  --target-records 100000 \
  --workers 16 \
  --batch-size 200 \
  --initial-delay 0.3 \
  --start-date 2025/07/01 \
  --end-date 2025/07/31 \
  --enable-retry \
  --max-retries 5
```

## 📊 Monitoring and Logs

### Real-time Monitoring
```bash
# Follow logs in real-time
sudo fpds-crawler-manager.py logs -f

# Check service metrics
sudo fpds-crawler-manager.py metrics

# View service status
sudo fpds-crawler-manager.py status
```

### Log Analysis
```bash
# View last 1000 lines
sudo fpds-crawler-manager.py logs -n 1000

# View log files directly
sudo fpds-crawler-manager.py file-logs -n 500

# Check log file sizes
ls -lh /var/log/fpds-crawler*.log
```

### Performance Monitoring
```bash
# Check memory usage
sudo systemctl show fpds-crawler --property=MemoryCurrent

# Check CPU usage
top -p $(pgrep -f fpds_high_performance.py)

# Check disk usage
df -h /home/fpds-crawler/crawler/result_data
```

## 🔧 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo fpds-crawler-manager.py status

# Check logs for errors
sudo fpds-crawler-manager.py logs -n 100

# Check file permissions
ls -la /home/fpds-crawler/crawler/
```

#### High Memory Usage
```bash
# Check memory usage
sudo fpds-crawler-manager.py metrics

# Reduce workers if needed
sudo fpds-crawler-manager.py stop
sudo fpds-crawler-manager.py install --workers 8 --target-records 10000
sudo fpds-crawler-manager.py start
```

#### Network Issues
```bash
# Check network connectivity
ping www.fpds.gov

# Check DNS resolution
nslookup www.fpds.gov

# Increase delays if rate limited
sudo fpds-crawler-manager.py install --initial-delay 1.0
```

### Log Locations
- **Service Logs:** `/var/log/fpds-crawler.log`
- **Error Logs:** `/var/log/fpds-crawler.error.log`
- **Systemd Logs:** `journalctl -u fpds-crawler`
- **Results:** `/home/fpds-crawler/crawler/result_data/`
- **Failed Requests:** `/home/fpds-crawler/crawler/failed_request_data/`

## 🏗️ Architecture

### File Structure
```
/home/fpds-crawler/
├── anaconda3/
│   └── envs/py311/          # Python environment
├── crawler/                 # Crawler code
│   ├── fpds_high_performance.py
│   ├── fpds-crawler-manager.py
│   ├── result_data/         # Output files
│   └── failed_request_data/ # Failed requests
└── .bashrc                  # Environment setup

/etc/
├── systemd/system/fpds-crawler.service  # Service definition
├── fpds-crawler/config.json             # Configuration
└── logrotate.d/fpds-crawler             # Log rotation

/var/log/
├── fpds-crawler.log         # Main logs
└── fpds-crawler.error.log   # Error logs
```

### Service Configuration
- **User:** `fpds-crawler`
- **Working Directory:** `/home/fpds-crawler/crawler`
- **Memory Limit:** 8 GB
- **CPU Limit:** 4 cores
- **Auto Restart:** On failure
- **Log Rotation:** Daily, 30 days retention

## 💰 Cost Estimation

### GCP VM Costs (Monthly)
- **e2-standard-2 (2 vCPU, 8 GB RAM):** $25-30
- **Storage (20 GB):** $2-3
- **Network Egress:** $5-10
- **Total:** $32-43/month

### Performance Expectations
- **Processing Rate:** 2-4 records/second
- **Daily Processing:** 1-2 hours
- **Monthly Processing:** 30-60 hours
- **Storage Growth:** ~5 GB/month

## 🔄 Automation

### Cron Job for Daily Crawling
```bash
# Edit crontab
sudo crontab -e

# Add daily crawling at 2 AM
0 2 * * * /usr/local/bin/fpds-crawler-manager.py restart
```

### Automated Monitoring
```bash
# Create monitoring script
cat > /home/fpds-crawler/monitor.sh << 'EOF'
#!/bin/bash
if ! systemctl is-active --quiet fpds-crawler; then
    echo "FPDS crawler service is down, restarting..."
    systemctl restart fpds-crawler
    echo "Service restarted at $(date)" >> /var/log/fpds-crawler-monitor.log
fi
EOF

chmod +x /home/fpds-crawler/monitor.sh

# Add to crontab (check every 5 minutes)
*/5 * * * * /home/fpds-crawler/monitor.sh
```

## 📈 Scaling

### For Higher Performance
- **VM Size:** Upgrade to e2-standard-4 (4 vCPU, 16 GB RAM)
- **Workers:** Increase to 32 workers
- **Batch Size:** Increase to 200-500
- **Cost:** $50-60/month

### For Monthly Processing
- **VM Size:** e2-standard-2 is sufficient
- **Processing Time:** 15-18 hours for full month
- **Storage:** 5-10 GB for monthly data
- **Cost:** $32-43/month

## 🔒 Security

### Service Security
- **User Isolation:** Dedicated `fpds-crawler` user
- **File Permissions:** Restricted access
- **System Protection:** Read-only system directories
- **Network Security:** No external ports exposed

### Data Security
- **Log Rotation:** Automatic cleanup
- **Backup:** Consider backing up `/home/fpds-crawler/crawler/result_data/`
- **Monitoring:** Service health checks
- **Updates:** Regular system updates

## 📞 Support

### Useful Commands
```bash
# Get help
fpds-crawler-manager.py --help

# Check all available commands
fpds-crawler-manager.py

# View configuration
sudo fpds-crawler-manager.py config

# Check system resources
htop
df -h
free -h
```

### Log Analysis
```bash
# Search for errors
sudo fpds-crawler-manager.py logs | grep -i error

# Search for specific patterns
sudo fpds-crawler-manager.py logs | grep "Progress:"

# Count successful extractions
sudo fpds-crawler-manager.py logs | grep "records" | wc -l
``` 