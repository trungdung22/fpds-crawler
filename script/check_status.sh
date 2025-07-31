#!/bin/bash
set -euo pipefail

### CONFIGURATION ###
PROJECT_ID="cloudmatos-saas-demo"
ZONE="us-central1-a"
INSTANCE_NAME="fpds-crawler-vm"

echo "🔍 FPDS Crawler VM Status Check"
echo "================================"

# Check if VM exists
VM_EXISTS=$(gcloud compute instances list --project="$PROJECT_ID" --filter="name=$INSTANCE_NAME" --format="value(name)" 2>/dev/null || echo "")

if [ -z "$VM_EXISTS" ]; then
    echo "❌ VM $INSTANCE_NAME does not exist."
    echo "💡 To create the VM, run: ./script/create_vm.sh"
    exit 1
fi

echo "✅ VM $INSTANCE_NAME exists."

# Get VM details
echo ""
echo "📋 VM Details:"
gcloud compute instances describe "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --format="table(
        name,
        machineType.basename,
        status,
        networkInterfaces[0].accessConfigs[0].natIP,
        creationTimestamp
    )"

# Get external IP
EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "🌐 Connection Information:"
echo "   SSH: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
echo "   Public IP: $EXTERNAL_IP"

# Check if VM is running
STATUS=$(gcloud compute instances describe "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --format='get(status)')

if [ "$STATUS" = "RUNNING" ]; then
    echo ""
    echo "✅ VM is running."
    echo ""
    echo "📋 Quick Commands:"
    echo "   SSH into VM: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
    echo "   Check service: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID --command='sudo python3 fpds-crawler-manager.py status'"
    echo "   View logs: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID --command='sudo python3 fpds-crawler-manager.py logs -n 20'"
else
    echo ""
    echo "⚠️ VM status: $STATUS"
    echo "💡 To start the VM: gcloud compute instances start $INSTANCE_NAME --zone=$ZONE"
fi

echo ""
echo "🔧 Management Commands:"
echo "   Start VM: gcloud compute instances start $INSTANCE_NAME --zone=$ZONE"
echo "   Stop VM: gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE"
echo "   Delete VM: ./script/delete_vm.sh" 