#!/bin/bash

# Usage: ./fix-space.sh SpaceName
# Example: ./fix-space.sh stock-momentum-agent

if [ -z "$1" ]; then
    echo "Usage: ./fix-space.sh <SpaceName>"
    exit 1
fi

SPACE_NAME=$1
USERNAME="RobBobin"
SOURCE_DIR="/Users/robin/git/agent/huggingface/my_agent"

cd /tmp
rm -rf "$SPACE_NAME"
git clone "https://huggingface.co/spaces/$USERNAME/$SPACE_NAME"
cd "$SPACE_NAME"

# Copy our files
cp "$SOURCE_DIR/my_agent.py" app.py
cp "$SOURCE_DIR/README.md" .

# Fix requirements - explicitly set without json
printf "smolagents\nyfinance\n" > requirements.txt

# Fix SDK version
sed -i '' 's/sdk_version: .*/sdk_version: 5.34.2/' README.md

git add .
git commit -m "Fix config and upload files"
git push

echo ""
echo "✅ Done! Now add HF_TOKEN secret at:"
echo "https://huggingface.co/spaces/$USERNAME/$SPACE_NAME/settings"
