# FPDS Crawler

A high-performance web crawler for extracting Federal Procurement Data System (FPDS) information with advanced features including multi-threading, retry mechanisms, and systemd service management.

## 🚀 Features

- **High Performance**: Multi-threaded crawling with configurable worker pools
- **Flexible Date Ranges**: Support for single or multiple month/year ranges
- **Advanced Filtering**: Filter by agency, vendor, and other criteria
- **Retry Mechanism**: Automatic retry with configurable attempts
- **Service Management**: Systemd service integration with monitoring
- **Data Export**: JSON and CSV output formats
- **Logging**: Comprehensive logging with error tracking
- **Rate Limiting**: Smart rate limiting to avoid API restrictions

## 📋 Requirements

- Python 3.8+
- Ubuntu 20.04+ (for VM deployment)
- Google Cloud Platform (for VM scripts)

## 🛠️ Installation

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/trungdung22/fpds-crawler.git
   cd fpds-crawler
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the crawler:**
   ```bash
   python3 fpds_high_performance.py --target-records 1000 --workers 4
   ```

### VM Deployment

1. **Create MongoDB VM:**
   ```bash
   ./script/mongodb/create_mongodb_vm.sh
   ```

2. **Create FPDS Crawler VM:**
   ```bash
   ./script/create_vm.sh
   ```

3. **Setup the crawler on VM:**
   ```bash
   sudo bash script/setup_vm.sh
   ```

## 🎯 Usage

### Direct Script Usage

```bash
# Basic usage
python3 fpds_high_performance.py --target-records 10000 --workers 8

# With date range
python3 fpds_high_performance.py \
    --target-records 50000 \
    --workers 16 \
    --start-date "2026/01/01" \
    --end-date "2026/01/31"

# With filters
python3 fpds_high_performance.py \
    --target-records 100000 \
    --workers 8 \
    --agency "DEPT OF DEFENSE" \
    --vendor "COMPANY NAME"
```

### Service Manager Usage

```bash
# Install service
sudo python3 fpds-crawler-manager.py install \
    --target-records 2000000 \
    --workers 16 \
    --month-year "1,2/2026"

# Start service
sudo python3 fpds-crawler-manager.py start

# Monitor logs
sudo python3 fpds-crawler-manager.py logs -f

# Check status
sudo python3 fpds-crawler-manager.py status
```

## ⚙️ Configuration

### Command Line Parameters

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--target-records` | Number of records to extract | 2000000 | `100000` |
| `--workers` | Number of worker threads | 16 | `8` |
| `--batch-size` | Batch size for processing | 100 | `50` |
| `--start-date` | Start date (YYYY/MM/DD) | Current month | `2026/01/01` |
| `--end-date` | End date (YYYY/MM/DD) | Current month | `2026/01/31` |
| `--initial-delay` | Delay between requests (seconds) | 0.5 | `1.0` |
| `--agency` | Filter by agency name | None | `"DEPT OF DEFENSE"` |
| `--vendor` | Filter by vendor name | None | `"COMPANY NAME"` |
| `--enable-retry` | Enable automatic retry | True | `--enable-retry` |
| `--max-retries` | Maximum retry attempts | 3 | `5` |

### Month/Year Format

The `--month-year` parameter supports flexible date ranges:

```bash
# Single month
--month-year "1/2026"      # January 2026

# Multiple months
--month-year "1,2/2026"    # January and February 2026
--month-year "1,2,3/2026"  # Q1 2026 (January, February, March)
--month-year "3,1,2/2026"  # Same as above (automatically sorted)
```

## 📊 Service Management

### Available Commands

```bash
# Installation and Setup
sudo python3 fpds-crawler-manager.py install [options]

# Service Control
sudo python3 fpds-crawler-manager.py start
sudo python3 fpds-crawler-manager.py stop
sudo python3 fpds-crawler-manager.py restart

# Monitoring
sudo python3 fpds-crawler-manager.py status
sudo python3 fpds-crawler-manager.py logs [-n lines] [-f]
sudo python3 fpds-crawler-manager.py file-logs [-n lines]
sudo python3 fpds-crawler-manager.py metrics

# Configuration
sudo python3 fpds-crawler-manager.py config
sudo python3 fpds-crawler-manager.py enable
sudo python3 fpds-crawler-manager.py disable

sudo systemctl daemon-reload
sudo systemctl stop fpds-crawler
sudo systemctl status fpds-crawler
sudo systemctl restart fpds-crawler
sudo journalctl -u fpds-crawler -n 50
```

### Service Files

- **Service File**: `/etc/systemd/system/fpds-crawler.service`
- **Configuration**: `/etc/fpds-crawler/config.json`
- **Logs**: `/var/log/fpds-crawler.log` and `/var/log/fpds-crawler.error.log`
- **Working Directory**: `/home/dungdo/fpds-crawler`

## 🗄️ MongoDB Integration

### Connection

The crawler can store data in MongoDB:

```bash
# MongoDB connection string
mongodb://admin_user:pass2024@<VM_IP>:27017/admin

# Test connection
mongosh "mongodb://admin_user:pass2024@35.184.140.117:27017/admin"
```

### VM Management

```bash
# Create MongoDB VM
./script/mongodb/create_mongodb_vm.sh

# Delete MongoDB VM
./script/mongodb/delete_mongodb_vm.sh

# Complete MongoDB setup (if SSH fails during creation)
./script/mongodb/complete_mongodb_setup.sh
```

## 📁 Project Structure

```
fpds-crawler/
├── fpds_high_performance.py      # Main crawler script
├── fpds-crawler-manager.py       # Service manager
├── fpds_enhanced_extractor.py    # Enhanced data extraction
├── fpds_field_mappings.py        # Field mapping definitions
├── mongo_service.py              # MongoDB integration
├── proxy_manager.py              # Proxy management
├── smart_rate_limiter.py         # Rate limiting
├── bulk_insert_helper.py         # Bulk data insertion
├── lib/                          # Core library modules
│   ├── config_manager.py
│   ├── crawler_framework.py
│   ├── llm_extractor.py
│   ├── rule_parser.py
│   └── utils.py
├── script/                       # Deployment scripts
│   ├── create_vm.sh             # Create FPDS crawler VM
│   ├── delete_vm.sh             # Delete FPDS crawler VM
│   ├── setup_vm.sh              # VM setup script
│   └── mongodb/                 # MongoDB VM scripts
│       ├── create_mongodb_vm.sh
│       ├── delete_mongodb_vm.sh
│       └── complete_mongodb_setup.sh
├── template/                     # HTML templates
├── data/                         # Output data directory
└── requirements.txt              # Python dependencies
```

## 🔧 Development

### Running Tests

```bash
# Test setup
python3 test_setup.py

# Test imports
python3 -c "import requests, bs4, lxml, selenium; print('All imports successful')"
```

### Adding New Features

1. **Extractors**: Add new extractors in `lib/llm_extractor.py`
2. **Field Mappings**: Update `fpds_field_mappings.py`
3. **Service Management**: Extend `fpds-crawler-manager.py`

## 📈 Performance Optimization

### Recommended Settings

```bash
# High Performance (16 cores, 32GB RAM)
--workers 16 --batch-size 100 --initial-delay 0.5

# Balanced (8 cores, 16GB RAM)
--workers 8 --batch-size 50 --initial-delay 1.0

# Conservative (4 cores, 8GB RAM)
--workers 4 --batch-size 25 --initial-delay 2.0
```

### Monitoring

```bash
# Real-time monitoring
sudo python3 fpds-crawler-manager.py logs -f

# Resource usage
sudo python3 fpds-crawler-manager.py metrics

# System monitoring
htop
iotop
```

## 🐛 Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   ```bash
   # Wait for VM to be ready
   gcloud compute ssh fpds-crawler-vm --zone=us-central1-c
   ```

2. **Service Won't Start**
   ```bash
   # Check logs
   sudo python3 fpds-crawler-manager.py logs
   sudo journalctl -u fpds-crawler -f
   ```

3. **MongoDB Connection Failed**
   ```bash
   # Test connection
   mongosh "mongodb://admin_user:pass2024@<IP>:27017/admin"
   ```

4. **Rate Limiting Issues**
   ```bash
   # Increase delays
   --initial-delay 2.0 --max-retries 5
   ```

### Debug Commands

```bash
# Check service status
sudo systemctl status fpds-crawler

# View detailed logs
sudo journalctl -u fpds-crawler -n 100

# Test network connectivity
curl -I https://www.fpds.gov

# Check disk space
df -h
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details

## 🔄 Changelog

### Version 1.0.0
- Initial release with high-performance crawling
- Systemd service integration
- MongoDB support
- Multi-month date range support
- Advanced filtering capabilities 