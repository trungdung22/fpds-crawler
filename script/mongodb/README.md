# FPDS MongoDB VM Scripts

This directory contains scripts for creating and managing MongoDB VMs for the FPDS crawler project.

## Scripts

### `create_mongodb_vm.sh`
Creates a MongoDB VM with the following features:
- **Instance Name**: `fpds-mongodb-vm`
- **Machine Type**: `e2-medium` (2 vCPUs, 4 GB memory)
- **Disk Size**: 30GB
- **Network**: Custom VPC (`fpds-cloudrun-vpc`) with subnet (`fpds-cloudrun-subnet`)
- **MongoDB**: Version 5.0 Community Edition
- **Security**: Authentication enabled with admin user
- **Firewall**: MongoDB port 27017 open, SSH restricted to Google Cloud IP ranges

### `delete_mongodb_vm.sh`
Deletes the MongoDB VM and associated resources:
- VM instance
- Firewall rules
- Subnet (if no other VMs are using it)
- VPC network (if no other VMs are using it)

## Usage

### Create MongoDB VM
```bash
./script/mongodb/create_mongodb_vm.sh
```

### Delete MongoDB VM
```bash
./script/mongodb/delete_mongodb_vm.sh
```

## Configuration

The scripts use the following configuration:
- **Project ID**: `cloudmatos-saas-demo`
- **Zone**: `us-central1-a`
- **MongoDB Admin User**: `admin_user`
- **MongoDB Admin Password**: `pass2024`

## Connection Information

After VM creation, you can connect to MongoDB using:
```bash
mongosh "mongodb://admin_user:pass2024@<VM_IP>:27017/admin"
```

Or SSH into the VM:
```bash
gcloud compute ssh fpds-mongodb-vm --zone=us-central1-a --project=cloudmatos-saas-demo
```

## Security Features

- MongoDB authentication enabled
- SSH access restricted to Google Cloud IP ranges
- MongoDB port 27017 open for remote connections
- Custom VPC network for isolation

## Differences from Original Script

- Instance name prefixed with `fpds-`
- Firewall rules use `fpds-mongodb` namespace
- Custom VPC network instead of default
- Enhanced cleanup that removes VPC/subnet if not in use
- Better error handling and status messages 