#!/bin/bash
# Download vectorstore from GitHub Release
# Run this script if vectorstore/ folder is missing

set -e

REPO="jerrxcc/MedBot"
RELEASE_TAG="v1.1.0"
ASSET_NAME="vectorstore.zip"

cd "$(dirname "$0")/.."

if [ -d "vectorstore" ] && [ -f "vectorstore/chroma.sqlite3" ]; then
    echo "[INFO] vectorstore/ already exists, skipping download"
    exit 0
fi

echo "[INFO] Downloading vectorstore from GitHub Release..."

# Download using gh CLI if available, otherwise curl
if command -v gh &> /dev/null; then
    gh release download "$RELEASE_TAG" --repo "$REPO" --pattern "$ASSET_NAME" --clobber
else
    # Fallback to curl
    DOWNLOAD_URL="https://github.com/$REPO/releases/download/$RELEASE_TAG/$ASSET_NAME"
    curl -L -o "$ASSET_NAME" "$DOWNLOAD_URL"
fi

echo "[INFO] Extracting vectorstore..."
unzip -o "$ASSET_NAME"
rm "$ASSET_NAME"

echo "[INFO] Done! vectorstore/ is ready."
