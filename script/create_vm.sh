#!/bin/bash
set -euo pipefail

### CONFIGURATION ###
PROJECT_ID="cloudmatos-saas-demo"
ZONE="us-central1-a"
INSTANCE_NAME="fpds-crawler-vm"
MACHINE_TYPE="e2-standard-4"  # 4 vCPUs, 16 GB memory for better performance
DISK_SIZE="200GB"
IMAGE_FAMILY="ubuntu-2204-lts"
IMAGE_PROJECT="ubuntu-os-cloud"
NETWORK="default"
FIREWALL_TAG="fpds-crawler"
FIREWALL_RULE_NAME="allow-common-${FIREWALL_TAG}"

echo "🚀 Creating FPDS Crawler VM..."

echo "✅ Using gcloud compute ssh for secure access"

### Create VM ###
gcloud compute instances create "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --machine-type="$MACHINE_TYPE" \
    --boot-disk-size="$DISK_SIZE" \
    --boot-disk-type=pd-standard \
    --image-family="$IMAGE_FAMILY" \
    --image-project="$IMAGE_PROJECT" \
    --tags="$FIREWALL_TAG" \
    --metadata-from-file=startup-script=script/setup_vm.sh

echo "⏳ VM created successfully. Waiting for startup script to begin..."
sleep 30

### Monitor setup progress ###
echo "📊 Monitoring setup progress..."
echo "Press Ctrl+C to stop monitoring (setup will continue in background)"
echo ""

# Function to check if VM is ready for SSH
check_vm_ready() {
    gcloud compute ssh "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --zone="$ZONE" \
        --command="echo 'VM is ready'" \
        --quiet >/dev/null 2>&1
}

# Function to get startup script logs
get_startup_logs() {
    gcloud compute ssh "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --zone="$ZONE" \
        --command="tail -n 50 /var/log/syslog | grep startup-script || echo 'No startup logs yet...'" \
        --quiet 2>/dev/null || echo "VM not ready for SSH yet..."
}

# Wait for VM to be ready and monitor logs
echo "⏳ Waiting for VM to be ready for SSH..."
while ! check_vm_ready; do
    echo "🔄 VM is still starting up... (waiting 30s)"
    sleep 30
done

echo "✅ VM is ready! Monitoring setup progress..."
echo ""

# Monitor setup progress with timestamps
start_time=$(date +%s)
last_log_line=""

while true; do
    current_logs=$(get_startup_logs)
    
    # Only print new log lines
    if [ "$current_logs" != "$last_log_line" ] && [ -n "$current_logs" ]; then
        current_time=$(date '+%H:%M:%S')
        elapsed=$(( $(date +%s) - start_time ))
        elapsed_min=$((elapsed / 60))
        elapsed_sec=$((elapsed % 60))
        
        echo "[$current_time] (${elapsed_min}m ${elapsed_sec}s) $current_logs"
        last_log_line="$current_logs"
    fi
    
    # Check if setup is complete
    if echo "$current_logs" | grep -q "FPDS Crawler VM setup completed successfully"; then
        echo ""
        echo "🎉 Setup completed successfully!"
        break
    fi
    
    # Check for errors
    if echo "$current_logs" | grep -q "ERROR\|FAILED\|failed"; then
        echo ""
        echo "❌ Setup encountered an error. Check logs for details."
        break
    fi
    
    sleep 10
done

### Create firewall rule to allow SSH and HTTP ###
echo "🔧 Creating firewall rules..."
gcloud compute firewall-rules create "$FIREWALL_RULE_NAME" \
    --project="$PROJECT_ID" \
    --network="$NETWORK" \
    --allow=tcp:22,tcp:80,tcp:443 \
    --source-ranges=0.0.0.0/0 \
    --target-tags="$FIREWALL_TAG" \
    --quiet || echo "Firewall rule already exists or failed."

### Get and display public IP address ###
EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "✅ VM $INSTANCE_NAME is ready."
echo "🌐 Public IP Address: $EXTERNAL_IP"
echo ""
echo "📋 Next steps:"
echo "1. SSH into the VM: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
echo "2. Test the setup: python3 test_setup.py"
echo "3. Install and start the service: sudo python3 fpds-crawler-manager.py install --help"
echo ""
echo "🔧 VM Setup includes:"
echo "   - Python3 and pip3"
echo "   - Required Python packages (requests, beautifulsoup4, lxml, etc.)"
echo "   - Git repository clone"
echo "   - User and service setup"
echo "🔒 Security features:"
echo "   - gcloud compute ssh for secure access"
echo "   - No public SSH keys required" 