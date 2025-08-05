#!/bin/bash

# Set variables
PROJECT_ID="cloudmatos-saas-demo"
ZONE="us-central1-c" # Change as needed
INSTANCE_NAME="mongodb-fpds-vm"
FIREWALL_RULE_NAME="fpds-allow-mongodb"
FIREWALL_RULE_NAME_2="fpds-allow-ssh-mongo"
# 1. Delete the VM instance
echo "Deleting VM instance $INSTANCE_NAME..."
gcloud compute instances delete $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --quiet

# 2. Delete the firewall rule
echo "Deleting firewall rule $FIREWALL_RULE_NAME..."
gcloud compute firewall-rules delete $FIREWALL_RULE_NAME \
    --project=$PROJECT_ID \
    --quiet

gcloud compute firewall-rules delete $FIREWALL_RULE_NAME_2 \
    --project=$PROJECT_ID \
    --quiet

# 3. Confirm deletion
echo "Resources deleted successfully."
