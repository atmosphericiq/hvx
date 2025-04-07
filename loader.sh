#!/bin/bash
IMPORT_FILE=$(mktemp)
SVC='1.0.0'
VERSION='1.0.16'
ENCODING="UTF-8"

echo "MACHINE HOSTNAME = $HOSTNAME"
echo "FILE VERSION = $FILE_VERSION"
echo "CORES = $CORES"
echo "LOADER VERSION = $VERSION"
echo "OUTPUT_SUBFOLDER = $OUTPUT_SUBFOLDER"
echo "RESISTIVITY_S3_GDB = $RESISTIVITY_S3_GDB"
echo "RESISTIVITY_GDB_FIELD_NAME_OHM_CM = $RESISTIVITY_GDB_FIELD_NAME_OHM_CM"
echo "PARALLELISM = $PARALLELISM"
echo "POWERLINE_HEIGHT = $POWERLINE_HEIGHT"
echo "POWERLINE_FILE = $POWERLINE_FILE"

# main stuff that gets loaded in here
echo "SEGMENT FILE = $SEGMENT_S3_PATH"
export BASENAME=$(basename $SEGMENT_S3_PATH)
echo "BASENAME = $BASENAME"
export FILENAME=$(echo "$BASENAME" | sed 's/\.gpkg$//')
echo "FILENAME = $FILENAME"

# get the job ID from environment vars
# https://docs.aws.amazon.com/batch/latest/userguide/job_env_vars.html
export JOB_ID=$AWS_BATCH_JOB_ID
echo "AWS JOB ID = $JOB_ID"
echo "AWS COMP ENVIRONMENT NAME = $AWS_BATCH_CE_NAME"
echo "AWS JOB QUEUE = $AWS_BATCH_JQ_NAME"

# special bash trapping for error events, where the exit
# code is anything other than 1
function onErrorEvent {
  THROWNERR=$?
  ERRCODE=${1}
  if [ $THROWNERR != "0" ]; then
    echo "THROWN=$THROWNERR"
    ERRCODE=$THROWNERR
  fi
  echo "Triggering error handler.."
  MESSAGE="$2"
  echo "ERRCODE=$ERRCODE"
  echo "MESSAGE=$MESSAGE"
  exit $ERRCODE
}
trap onErrorEvent ERR
# END of trap code

echo "make sure SEGMENT_S3_PATH is not null.."
[[ -z "$SEGMENT_S3_PATH" ]] && onErrorEvent 1 "ERROR: SEGMENT_S3_PATH is empty"

echo "copying file from s3 location $SEGMENT_S3_PATH -> $BASENAME"
aws s3 cp "$SEGMENT_S3_PATH" $BASENAME --quiet

echo "copying resistivity and powerline files"
aws s3 cp "$RESISTIVITY_S3_GDB" lp_resistivity.3857.gdb --recursive --quiet

echo "copying powerline file"
aws s3 cp "$POWERLINE_FILE" powerline.3857.gpkg  --quiet

echo "copying decoupler records"
aws s3 cp s3://edi-hv-analysis/decouplers.3857.gpkg decouplers.3857.gpkg --quiet

echo "copy ACPS records"
aws s3 cp s3://edi-hv-analysis/LP.2024.latest_survey.3857.gpkg LP.2024.latest_survey.3857.gpkg --quiet

echo "confirming we have powerline layer and resistivity layers"
ogrinfo /app/powerline.3857.gpkg
ogrinfo /app/lp_resistivity.3857.gdb

echo "Running fields.py script"
python3 fields.py --continuity-shapefile $BASENAME \
  --parallelism $PARALLELISM \
  --base-height $POWERLINE_HEIGHT \
  --decouplers-gpkg /app/decouplers.3857.gpkg \
  --annual-survey-gpkg /app/LP.2024.latest_survey.3857.gpkg \
  --resistivity-file /app/lp_resistivity.3857.gdb \
  --resistivity-field-name $RESISTIVITY_GDB_FIELD_NAME_OHM_CM \
  --output-shapefile "$FILENAME.scored.3857.gdb" \
  --powerline-file /app/powerline.3857.gpkg

# print result code for last command
echo "fields.py result code = $?"

# turn it into a gpkg now
echo "Fields done. Reprojecting result -> 4326 GPKG"
ogr2ogr "$FILENAME.scored.4326.gpkg" "$FILENAME.scored.3857.gdb" -t_srs epsg:4326 -of GPKG

export FINALS3KEY="s3://edi-hv-analysis/scored/$OUTPUT_SUBFOLDER/$FILENAME.scored.4326.gpkg"
echo "Copying results to S3  = $FINALS3KEY"
aws s3 cp $FILENAME.scored.4326.gpkg $FINALS3KEY --quiet

echo "All done"
