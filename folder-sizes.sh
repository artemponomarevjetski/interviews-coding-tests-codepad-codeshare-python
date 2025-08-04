#!/bin/bash

# Define folders
FOLDERS=("Projects1" "Projects" "Projects_Combined")

# Header for output
echo "Folder Analysis:"
echo "----------------------------------------------"
printf "%-20s %-10s %-10s\n" "Folder Name" "Size" "File Count"
echo "----------------------------------------------"

# Loop through each folder
for folder in "${FOLDERS[@]}"; do
    if [ -d "$HOME/Desktop/$folder" ]; then
        SIZE=$(du -sh "$HOME/Desktop/$folder" | awk '{print $1}')
        FILES=$(find "$HOME/Desktop/$folder" -type f | wc -l)
        printf "%-20s %-10s %-10s\n" "$folder" "$SIZE" "$FILES"
    else
        printf "%-20s %-10s %-10s\n" "$folder" "Not Found" "N/A"
    fi
done

echo "----------------------------------------------"
echo "Analysis complete!"

