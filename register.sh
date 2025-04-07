#!/bin/bash

aws batch register-job-definition \
    --job-definition-name "hv-analysis" \
    --type "container" \
    --container-properties '{
        "logConfiguration": {
          "logDriver": "awslogs",
          "options": {
            "awslogs-group": "hv-analysis",
            "awslogs-region": "us-east-1"
          }
        },
        "image": "384504264639.dkr.ecr.us-east-1.amazonaws.com/hv-loader:latest",
        "vcpus": 96,
        "memory": 190000,
        "command": ["./loader.sh"],
        "environment": []
    }'
