#!/bin/bash
aws ecr get-login-password --region us-east-1 | docker login  \
  --username AWS \
  --password-stdin 384504264639.dkr.ecr.us-east-1.amazonaws.com

ECR="384504264639.dkr.ecr.us-east-1.amazonaws.com/hv-loader"

docker build . -t hv-loader
docker tag hv-loader:latest $ECR:latest
docker push $ECR:latest 
