#!/bin/bash

# Infinite loop to capture and email a snapshot every 10 seconds
while true; do
    # Capture the screenshot and save it to ~/temp
    screencapture -C -D1 -x ~/temp/snap_latest.png

    # Send the new screenshot via msmtp to your Yahoo email
    echo "Sending snapshot..." | msmtp artem_ponomarev@yahoo.com

    # Wait for 10 seconds before the next snapshot
    sleep 10
done
