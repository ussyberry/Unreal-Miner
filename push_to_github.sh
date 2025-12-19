#!/bin/bash

echo "=== Unreal Miner Repository Push Script ==="
echo ""
echo "This script will help you push the optimized repository to GitHub."
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "unreal_miner" ]; then
    echo "Error: Please run this script from the Unreal-Miner root directory"
    exit 1
fi

echo "✅ Repository structure verified"
echo ""

# Show current status
echo "📊 Current git status:"
git status
echo ""

# Show commit that needs to be pushed
echo "📝 Latest commit to push:"
git log --oneline -1
echo ""

echo "🔐 To push to GitHub, you need to authenticate:"
echo ""
echo "Option 1: Personal Access Token (Recommended)"
echo "1. Go to GitHub → Settings → Developer settings → Personal access tokens"
echo "2. Generate new token with 'repo' permissions"
echo "3. Copy the token (starts with 'ghp_')"
echo "4. Run: git remote set-url origin https://YOUR_TOKEN@github.com/ussyberry/Unreal-Miner.git"
echo "5. Run: git push origin main"
echo ""
echo "Option 2: SSH Key"
echo "1. Run: ssh-keygen -t ed25519 -C 'usman.kadiri@gmail.com'"
echo "2. Add ~/.ssh/id_ed25519.pub to GitHub SSH settings"
echo "3. Run: git remote set-url origin git@github.com:ussyberry/Unreal-Miner.git"
echo "4. Run: git push origin main"
echo ""
echo "Option 3: GitHub CLI"
echo "1. Install: sudo apt install gh (or download from github.com/cli)"
echo "2. Run: gh auth login"
echo "3. Run: git push origin main"
echo ""

echo "🚀 Once authenticated, your optimized repository will be live on GitHub!"
echo "📈 Ready for investor review with funding documentation"