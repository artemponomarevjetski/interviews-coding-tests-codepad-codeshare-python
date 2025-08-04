#!/bin/bash

# Directories to compare
DIR1="/Users/artem.ponomarev/Desktop/Projects"
DIR2="/Users/artem.ponomarev/Projects"

# Ensure both directories exist
if [ ! -d "$DIR1" ] || [ ! -d "$DIR2" ]; then
  echo "❌ Error: One or both directories do not exist."
  exit 1
fi

echo "🔍 Comparing folders: $DIR1 vs. $DIR2"
echo "================================================"

# 1️⃣ Check for missing or extra files
MISSING_IN_DIR1=$(diff -qr --exclude=".DS_Store" --exclude="venv" "$DIR1" "$DIR2" | grep "Only in $DIR2" | wc -l)
MISSING_IN_DIR2=$(diff -qr --exclude=".DS_Store" --exclude="venv" "$DIR1" "$DIR2" | grep "Only in $DIR1" | wc -l)

# 2️⃣ Check for different file contents (ignores metadata)
DIFFERENT_FILES=$(diff -qr --exclude=".DS_Store" --exclude="venv" "$DIR1" "$DIR2" | grep "Files" | wc -l)

# 3️⃣ Final Decision
if [[ "$MISSING_IN_DIR1" -eq 0 && "$MISSING_IN_DIR2" -eq 0 && "$DIFFERENT_FILES" -eq 0 ]]; then
  echo "✅ Both folders are **identical** (same files, same content)."
else
  echo "❌ Differences found between the two folders!"
  echo "------------------------------------------------"

  if [[ "$MISSING_IN_DIR1" -gt 0 ]]; then
    echo "📂 Files missing in $DIR1:"
    diff -qr --exclude=".DS_Store" --exclude="venv" "$DIR1" "$DIR2" | grep "Only in $DIR2"
  fi

  if [[ "$MISSING_IN_DIR2" -gt 0 ]]; then
    echo "📂 Files missing in $DIR2:"
    diff -qr --exclude=".DS_Store" --exclude="venv" "$DIR1" "$DIR2" | grep "Only in $DIR1"
  fi

  if [[ "$DIFFERENT_FILES" -gt 0 ]]; then
    echo "🔍 Files with **different content**:"
    diff -qr --exclude=".DS_Store" --exclude="venv" "$DIR1" "$DIR2" | grep "Files"
  fi
fi

exit 0

