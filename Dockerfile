FROM 384504264639.dkr.ecr.us-east-1.amazonaws.com/gis-toolkit:latest

COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

# COPY over the main HVAC files
COPY loader.sh /app/loader.sh
COPY fields.py /app/fields.py
COPY field_helper.py /app/field_helper.py
COPY split_line.py /app/split_line.py
COPY split_line2.py /app/split_line2.py

# make sure we dont use local version of lib c++
RUN rm -rf /usr/local/lib/libstdc++.so.6

ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:/usr/local/lib

WORKDIR /app
