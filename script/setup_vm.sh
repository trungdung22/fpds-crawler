#!/bin/bash
set -euo pipefail

# Log all output to syslog
exec 1> >(tee -a /var/log/syslog)
exec 2> >(tee -a /var/log/syslog >&2)

echo "Starting FPDS Crawler VM setup..."

# Update system packages
echo "Updating system packages..."
apt-get update -y

# Install Python3 and pip3
echo "Installing Python3 and pip3..."
apt-get install -y python3 python3-pip python3-venv

# Install system dependencies
echo "Installing system dependencies..."
apt-get install -y \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libssl-dev \
    zlib1g-dev

# Upgrade pip
echo "⬆Upgrading pip..."
python3 -m pip install --upgrade pip

# Install Python packages
echo "Installing Python packages..."
python3 -m pip install \
    requests \
    beautifulsoup4 \
    lxml \
    selenium \
    webdriver-manager \
    pandas \
    numpy \
    tqdm \
    psutil \
    python-dateutil

# Setup FPDS crawler in /home/dungdo
echo "Setting up FPDS crawler in /home/dungdo..."
cd /home/dungdo

# Clone the repository
echo "Cloning FPDS crawler repository..."
git clone https://github.com/trungdung22/fpds-crawler.git || echo "Repository already exists"

# Create necessary directories
mkdir -p fpds-crawler/result_data
mkdir -p fpds-crawler/failed_request_data

# Set permissions
chmod 755 fpds-crawler
chmod 755 fpds-crawler/result_data
chmod 755 fpds-crawler/failed_request_data

# Make scripts executable
chmod +x fpds-crawler/*.py

# Create log directories and set permissions
echo "📝 Setting up log directories..."
mkdir -p /var/log
touch /var/log/fpds-crawler.log
touch /var/log/fpds-crawler.error.log
chown dungdo:dungdo /var/log/fpds-crawler*.log
chmod 644 /var/log/fpds-crawler*.log

# Create config directory
echo "⚙️ Setting up config directory..."
mkdir -p /etc/fpds-crawler
chown dungdo:dungdo /etc/fpds-crawler

# Secure SSH configuration for gcloud compute ssh
# echo "🔒 Configuring SSH for gcloud compute ssh..."
# sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
# sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config
# systemctl restart ssh

# Test Python installation
echo "🧪 Testing Python installation..."
sudo -u dungdo python3 -c "
import requests
import bs4
import lxml
import selenium
print('✅ All required packages installed successfully!')
"

# Create a simple test script
echo "📋 Creating test script..."
cat > /home/dungdo/test_setup.py << 'EOF'
#!/usr/bin/env python3
import sys
import requests
import bs4
import lxml
import selenium

def test_imports():
    print("Testing imports...")
    try:
        import requests
        print("✅ requests imported successfully")
    except ImportError as e:
        print(f"❌ requests import failed: {e}")
        return False
    
    try:
        import bs4
        print("✅ beautifulsoup4 imported successfully")
    except ImportError as e:
        print(f"❌ beautifulsoup4 import failed: {e}")
        return False
    
    try:
        import lxml
        print("✅ lxml imported successfully")
    except ImportError as e:
        print(f"❌ lxml import failed: {e}")
        return False
    
    try:
        import selenium
        print("✅ selenium imported successfully")
    except ImportError as e:
        print(f"❌ selenium import failed: {e}")
        return False
    
    return True

def test_network():
    print("\nTesting network connectivity...")
    try:
        response = requests.get("https://www.fpds.gov", timeout=10)
        print(f"✅ Network connectivity OK (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Network connectivity failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 FPDS Crawler Setup Test")
    print("=" * 40)
    
    imports_ok = test_imports()
    network_ok = test_network()
    
    if imports_ok and network_ok:
        print("\n🎉 All tests passed! Setup is complete.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the setup.")
        sys.exit(1)
EOF

chmod +x /home/dungdo/test_setup.py
chown dungdo:dungdo /home/dungdo/test_setup.py

# Run test
echo "🧪 Running setup test..."
sudo -u dungdo python3 /home/dungdo/test_setup.py

# Create usage instructions
echo "📖 Creating usage instructions..."
cat > /home/dungdo/README_VM_SETUP.md << 'EOF'
# FPDS Crawler VM Setup Complete

## Quick Start

1. **Test the setup:**
   ```bash
   python3 test_setup.py
   ```

2. **View available commands:**
   ```bash
   sudo python3 fpds-crawler-manager.py --help
   ```

3. **Install and start the service:**
   ```bash
   sudo python3 fpds-crawler-manager.py install --target-records 10000 --workers 8
   sudo python3 fpds-crawler-manager.py start
   ```

4. **Check service status:**
   ```bash
   sudo python3 fpds-crawler-manager.py status
   ```

5. **View logs:**
   ```bash
   sudo python3 fpds-crawler-manager.py logs
   ```

## Direct Script Usage

You can also run the crawler directly:

```bash
python3 fpds_high_performance.py --target-records 10000 --workers 8
```

## Files and Directories

- `/home/dungdo/fpds-crawler/` - Main application directory
- `/var/log/fpds-crawler.log` - Application logs
- `/var/log/fpds-crawler.error.log` - Error logs
- `/etc/fpds-crawler/config.json` - Service configuration
- `result_data/` - Extracted data output
- `failed_request_data/` - Failed requests for retry

## Monitoring

- Service status: `sudo systemctl status fpds-crawler`
- Real-time logs: `sudo journalctl -u fpds-crawler -f`
- Resource usage: `sudo python3 fpds-crawler-manager.py metrics`
EOF

chown dungdo:dungdo /home/dungdo/README_VM_SETUP.md

echo "✅ FPDS Crawler VM setup completed successfully!"
echo "📖 Check /home/dungdo/README_VM_SETUP.md for usage instructions"
echo "🧪 Run 'python3 test_setup.py' to verify the installation" 