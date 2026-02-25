#!/bin/bash
echo "Creating S3 bucket for ImagineAI..."
awslocal s3 mb s3://imagineai-images
awslocal s3api put-bucket-cors --bucket imagineai-images --cors-configuration '{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "AllowedOrigins": ["http://localhost:4200", "http://localhost:8000"],
      "MaxAgeSeconds": 3600
    }
  ]
}'
echo "S3 bucket created successfully"
