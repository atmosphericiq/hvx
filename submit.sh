#!/bin/bash

SEGMENT=$2
CUSTOMER=$1

if [ -z "$SEGMENT" ]; then
    echo "Error: SEGMENT is not set. Please provide a segment value as the second argument."
    echo "Usage: ./submit.sh <customer_id> <segment>"
    exit 1
fi
if [ -z "$CUSTOMER" ]; then
    echo "Error: CUSTOMER is not set. Please provide a customer ID as the first argument."
    echo "Usage: ./submit.sh <customer_id> <segment>"
    exit 1
fi

# s3://edi-hv-analysis/lp_resistivity.3857.gdb
# GTM resistivity

aws batch submit-job \
    --job-name "$(uuid)" \
    --job-queue "hv-analysis" \
    --job-definition "hv-analysis" \
    --container-overrides '{
        "environment": [
            {
                "name": "PARALLELISM",
                "value": "96"
            },
            {
                "name": "OUTPUT_SUBFOLDER",
                "value": "2024-12-18"
            },
            {
                "name": "POWERLINE_HEIGHT",
                "value": "14"
            },
            {
                "name": "RESISTIVITY_S3_GDB",
                "value": "s3://edi-hv-analysis/lp_resistivity.3857.gdb"
            },
            {
                "name": "RESISTIVITY_GDB_FIELD_NAME_OHM_CM",
                "value": "resistivity_ohm_cm"
            },
            {
                "name": "SEGMENT_S3_PATH",
                "value": "s3://edi-hv-analysis/segments/'$CUSTOMER'/'$SEGMENT'.gpkg"
            },
            {
              "name": "AWS_ACCESS_KEY_ID",
              "value": "'$AWS_ACCESS_KEY_ID'"
            },
            {
              "name": "AWS_SECRET_ACCESS_KEY",
              "value": "'$AWS_SECRET_ACCESS_KEY'"
            },
            {
                "name": "AWS_DEFAULT_REGION",
                "value": "'$AWS_DEFAULT_REGION'"
            }
        ]
    }'
