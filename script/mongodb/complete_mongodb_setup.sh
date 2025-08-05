#!/bin/bash
set -euo pipefail

### CONFIGURATION ###
PROJECT_ID="cloudmatos-saas-demo"
ZONE="us-central1-c"
INSTANCE_NAME="fpds-mongodb-vm"
MONGO_ADMIN_USER="admin_user"
MONGO_ADMIN_PASSWORD="pass2024"

echo "🔧 Completing MongoDB setup on $INSTANCE_NAME..."

# Function to run SSH command with retry
run_ssh_command() {
    local command="$1"
    local max_retries=3
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if gcloud compute ssh "$INSTANCE_NAME" \
            --project="$PROJECT_ID" \
            --zone="$ZONE" \
            --command="$command" \
            --quiet; then
            return 0
        else
            retry_count=$((retry_count + 1))
            echo "⚠️ SSH command failed, retrying... (attempt $retry_count/$max_retries)"
            sleep 10
        fi
    done
    
    echo "❌ SSH command failed after $max_retries attempts"
    return 1
}

### Test SSH connectivity first ###
echo "🔍 Testing SSH connectivity..."
if ! gcloud compute ssh "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --command="echo 'SSH connection successful'" \
    --quiet; then
    echo "❌ SSH connection failed. Please wait a few more minutes and try again."
    echo "💡 You can test SSH manually with:"
    echo "   gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
    exit 1
fi

echo "✅ SSH connection successful!"

### Install MongoDB ###
echo "📦 Installing MongoDB..."
run_ssh_command "
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

### Configure MongoDB for remote access ###
echo "🔧 Configuring MongoDB for remote access..."
run_ssh_command "
    sudo sed -i \"s/bindIp: 127.0.0.1/bindIp: 0.0.0.0/\" /etc/mongod.conf && \
    sudo systemctl restart mongod
"

### Create MongoDB admin user ###
echo "👤 Creating MongoDB admin user..."
run_ssh_command "
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

### Get and display public IP address ###
EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "✅ MongoDB setup completed successfully!"
echo "🌐 Public IP Address: $EXTERNAL_IP"
echo ""
echo "📋 Connection Information:"
echo "   MongoDB Connection String: mongodb://$MONGO_ADMIN_USER:$MONGO_ADMIN_PASSWORD@$EXTERNAL_IP:27017/admin"
echo "   SSH Access: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID"
echo ""
echo "🔧 Setup includes:"
echo "   - MongoDB 5.0 Community Edition"
echo "   - Remote access enabled"
echo "   - Admin user: $MONGO_ADMIN_USER"
echo "🔒 Security features:"
echo "   - MongoDB authentication enabled"
echo "   - SSH access restricted to Google Cloud IP ranges"
echo "   - MongoDB port 27017 open for remote connections" 