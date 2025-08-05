#!/bin/bash
set -euo pipefail

### CONFIGURATION ###
PROJECT_ID="cloudmatos-saas-demo"
ZONE="us-central1-c"
INSTANCE_NAME="fpds-crawler-vm"
FIREWALL_TAG="fpds-crawler"
FIREWALL_RULE_NAME="allow-common-${FIREWALL_TAG}"

echo "🗑️ Starting FPDS Crawler VM cleanup..."

# Check if VM exists
VM_EXISTS=$(gcloud compute instances list --project="$PROJECT_ID" --filter="name=$INSTANCE_NAME" --format="value(name)" 2>/dev/null || echo "")

if [ -z "$VM_EXISTS" ]; then
    echo "⚠️ VM $INSTANCE_NAME does not exist. Skipping VM deletion."
else
    echo "🖥️ Deleting VM: $INSTANCE_NAME"
    gcloud compute instances delete "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --zone="$ZONE" \
        --quiet
    
    echo "✅ VM $INSTANCE_NAME deleted successfully."
fi

# Delete firewall rule
echo "🔥 Deleting firewall rule: $FIREWALL_RULE_NAME"
gcloud compute firewall-rules delete "$FIREWALL_RULE_NAME" \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || echo "⚠️ Firewall rule $FIREWALL_RULE_NAME does not exist or already deleted."

echo "✅ FPDS Crawler VM cleanup completed!"
echo ""
echo "🧹 Cleaned up resources:"
echo "   - VM: $INSTANCE_NAME"
echo "   - Firewall rule: $FIREWALL_RULE_NAME"
echo ""
echo "💡 To recreate the VM, run: ./script/create_vm.sh" 