#!/bin/bash

# Directories to compare
LARGER_DIR="/Users/artem.ponomarev/Projects"
SMALLER_DIR="/Users/artem.ponomarev/Desktop/Projects"

# Ensure both directories exist
if [ ! -d "$LARGER_DIR" ] || [ ! -d "$SMALLER_DIR" ]; then
  echo "❌ Error: One or both directories do not exist."
  exit 1
fi

echo "🔍 Checking if $SMALLER_DIR is a **strict subset** of $LARGER_DIR"
echo "================================================================"

# 1️⃣ Generate file lists (ignoring system files)
find "$SMALLER_DIR" -type f ! -name ".DS_Store" ! -path "*/__MACOSX/*" ! -path "*/venv/*" 2>/dev/null | sed "s|$SMALLER_DIR/||" | sort > subset_files.txt
find "$LARGER_DIR" -type f ! -name ".DS_Store" ! -path "*/__MACOSX/*" ! -path "*/venv/*" 2>/dev/null | sed "s|$LARGER_DIR/||" | sort > parent_files.txt

# 2️⃣ Find missing files in the parent folder
MISSING_IN_PARENT=$(comm -23 subset_files.txt parent_files.txt | wc -l)

# 3️⃣ Generate checksums for files that exist in both folders
find "$SMALLER_DIR" -type f ! -name ".DS_Store" -exec md5 {} + 2>/dev/null | sed "s|$SMALLER_DIR/||" | sort > subset_checksums.txt
find "$LARGER_DIR" -type f ! -name ".DS_Store" -exec md5 {} + 2>/dev/null | sed "s|$LARGER_DIR/||" | sort > parent_checksums.txt

# 4️⃣ Compare checksums to find differing file content
DIFFERENT_FILES=$(diff subset_checksums.txt parent_checksums.txt | wc -l)

# 5️⃣ Final Decision
if [[ "$MISSING_IN_PARENT" -eq 0 && "$DIFFERENT_FILES" -eq 0 ]]; then
  echo "✅ $SMALLER_DIR is a **strict subset** of $LARGER_DIR (all files exist and match)."
else
  echo "❌ $SMALLER_DIR is **NOT** a strict subset of $LARGER_DIR!"
  echo "----------------------------------------------------------------"

  if [[ "$MISSING_IN_PARENT" -gt 0 ]]; then
    echo "📂 Files in $SMALLER_DIR that are **missing** from $LARGER_DIR:"
    comm -23 subset_files.txt parent_files.txt
  fi

  if [[ "$DIFFERENT_FILES" -gt 0 ]]; then
    echo "🔍 Files that exist in both but have **different content**:"
    diff subset_checksums.txt parent_checksums.txt
  fi
fi

# Cleanup temporary files
rm subset_files.txt parent_files.txt subset_checksums.txt parent_checksums.txt

exit 0

