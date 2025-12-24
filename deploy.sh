#!/bin/bash
# Deploy Stock Analysis Agent to Hugging Face Spaces
# This script manually uploads files to avoid agent.push_to_hub() 
# which incorrectly adds "json" to requirements.txt

set -e  # Exit on error

SPACE_NAME="RobBobin/stock-analysis-agent"
TEMP_DIR="/tmp/stock-analysis-agent"

echo "=== Deploying to $SPACE_NAME ==="

# Clean up any previous temp directory
rm -rf "$TEMP_DIR"

# Clone the Space repo
echo "Cloning Space..."
git clone "https://huggingface.co/spaces/$SPACE_NAME" "$TEMP_DIR"

# Copy our files
echo "Copying files..."
cp "$(dirname "$0")/my_agent.py" "$TEMP_DIR/app.py"
cp "$(dirname "$0")/README.md" "$TEMP_DIR/README.md"

# CRITICAL: Set requirements.txt manually
# DO NOT include "json" - it's a built-in Python module, not a pip package
echo "Setting requirements.txt..."
printf "smolagents\nyfinance\n" > "$TEMP_DIR/requirements.txt"

# Commit and push
cd "$TEMP_DIR"
git add .
git commit -m "Update agent - $(date '+%Y-%m-%d %H:%M')" || echo "No changes to commit"
git push

echo "=== Deploy complete! ==="
echo "View at: https://huggingface.co/spaces/$SPACE_NAME"
