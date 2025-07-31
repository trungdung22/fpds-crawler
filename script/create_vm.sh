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

echo "⏳ Waiting 60s for VM to initialize..."
sleep 60

### Create firewall rule to allow SSH and HTTP ###
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

echo "✅ VM $INSTANCE_NAME is ready."
echo "🌐 Public IP Address: $EXTERNAL_IP"
echo ""
echo "📋 Next steps:"
echo "1. SSH into the VM: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
echo "2. Check setup progress: tail -f /var/log/syslog | grep startup-script"
echo "3. Once setup is complete, run: sudo python3 fpds-crawler-manager.py install --help"
echo ""
echo "🔧 VM Setup includes:"
echo "   - Python3 and pip3"
echo "   - Required Python packages (requests, beautifulsoup4, lxml, etc.)"
echo "   - Git repository clone"
echo "   - User and service setup"
echo "🔒 Security features:"
echo "   - gcloud compute ssh for secure access"
echo "   - No public SSH keys required" 