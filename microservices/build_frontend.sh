#!/bin/bash
# Script to build frontend and copy to gateway

# Build frontend
cd /Users/kadirs/Dev/local_deployment_fixed_final_v8/frontend
npm install
npm run build

# Copy build to gateway
cp -r /Users/kadirs/Dev/local_deployment_fixed_final_v8/frontend/build/* /Users/kadirs/Dev/local_deployment_fixed_final_v8/microservices/gateway/

echo "Frontend built and copied to gateway"