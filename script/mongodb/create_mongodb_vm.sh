#!/bin/bash

# mongosh "mongodb://user_admin:pass2024@34.143.183.15:27017"
# Set variables
PROJECT_ID="cloudmatos-saas-demo"
ZONE="us-central1-c" # Change as needed
INSTANCE_NAME="mongodb-fpds-vm"
MACHINE_TYPE="e2-medium"
DISK_SIZE="200GB"
NETWORK="default"
FIREWALL_RULE_NAME="fpds-allow-mongodb"
MONGO_ADMIN_USER="admin_user"
MONGO_ADMIN_PASSWORD="pass2024"
TARGET_FIREWALL_RULE_NAME="fpds-allow-mongodb"


###
# # 1. Create a VM instance
gcloud compute instances create $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --boot-disk-size=$DISK_SIZE \
    --boot-disk-type=pd-standard \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --tags=$TARGET_FIREWALL_RULE_NAME

# # 2. Allow time for VM to start
echo "Waiting for VM to start..."
sleep 90

# 6. Create a firewall rule to allow access to MongoDB
gcloud compute firewall-rules create $FIREWALL_RULE_NAME \
    --project=$PROJECT_ID \
    --network=$NETWORK \
    --allow=tcp:27017 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=$TARGET_FIREWALL_RULE_NAME

# # TARGET_FIREWALL_RULE_NAME="allow-ssh"

gcloud compute firewall-rules create fpds-allow-ssh-mongo \
    --project=$PROJECT_ID \
    --network=$NETWORK \
    --allow=tcp:22 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=$TARGET_FIREWALL_RULE_NAME

gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
    sudo apt-get update && \
    sudo apt-get install -y gnupg curl && \
    curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
    sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor && \
    echo \"deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse\" | \
    sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list && \
    sudo apt-get update && \
    sudo apt-get install -y mongodb-org && \
    sudo systemctl start mongod && \
    sudo systemctl enable mongod
"

# 4. Configure MongoDB to allow remote access
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
    sudo sed -i \"s/bindIp: 127.0.0.1/bindIp: 0.0.0.0/\" /etc/mongod.conf && \
    sudo systemctl restart mongod
"

gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
    mongosh --eval 'db.createUser({
        user: \"$MONGO_ADMIN_USER\",
        pwd: \"$MONGO_ADMIN_PASSWORD\",
        roles:[
            \"userAdminAnyDatabase\",
            \"dbAdminAnyDatabase\",
            \"readWriteAnyDatabase\",
            \"dbAdmin\"
        ]
    })' admin && \
    sudo sed -i '/^#security:/ s/#//' /etc/mongod.conf && \
    sudo sed -i '/^security:/a\  authorization: enabled' /etc/mongod.conf && \
    sudo systemctl restart mongod
"

# 7. Output VM external IP for connection
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo ""
echo "✅ MongoDB VM $INSTANCE_NAME is ready."
echo "🌐 Public IP Address: $EXTERNAL_IP"
echo ""
echo "📋 Connection Information:"
echo "   MongoDB Connection String: mongodb://$MONGO_ADMIN_USER:$MONGO_ADMIN_PASSWORD@$EXTERNAL_IP:27017/admin"
echo "   SSH Access: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
echo ""
echo "🔧 VM Setup includes:"
echo "   - MongoDB 7.0 Community Edition"
echo "   - Remote access enabled"
echo "   - Admin user: $MONGO_ADMIN_USER"
echo "🔒 Security features:"
echo "   - MongoDB authentication enabled"
echo "   - SSH access open to all IPs (for testing)"
echo "   - MongoDB port 27017 open for remote connections"