#!/bin/bash
set -euo pipefail

echo "🚀 FPDS Crawler Deployment Script"
echo "=================================="

echo "✅ Using gcloud compute ssh for secure access"

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK is not installed. Please install it first."
    echo "   Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with gcloud. Please run: gcloud auth login"
    exit 1
fi

# Check if project is set
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No project set. Please run: gcloud config set project cloudmatos-saas-demo"
    exit 1
fi

echo "✅ Using project: $PROJECT_ID"

# Ask user for confirmation
echo ""
echo "This will create a VM with the following specifications:"
echo "  - Machine type: e2-standard-4 (4 vCPUs, 16 GB memory)"
echo "  - Disk: 200GB"
echo "  - OS: Ubuntu 22.04 LTS"
echo "  - Zone: us-central1-a"
echo "  - SSH access: gcloud compute ssh (secure)"
echo "  - No SSH keys required"
echo ""
read -p "Do you want to continue? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled."
    exit 1
fi

# Create VM
echo ""
echo "🖥️ Creating VM..."
./script/create_vm.sh

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Wait a few minutes for the VM setup to complete"
echo "2. SSH into the VM: gcloud compute ssh fpds-crawler-vm --zone=us-central1-a --project=$PROJECT_ID"
echo "3. Run: python3 test_setup.py"
echo "4. Start the service: sudo python3 fpds-crawler-manager.py install --target-records 10000"
echo ""
echo "📖 For detailed instructions, see: script/README_DEPLOYMENT.md"
echo "🗑️ To delete the VM later, run: ./script/delete_vm.sh" 