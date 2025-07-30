#!/bin/bash

# TrendzPortal Git Workflow Helper
# This script helps manage the development workflow

set -e

echo "🚀 TrendzPortal Git Workflow Helper"
echo "===================================="
echo

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# Show available branches
echo "🌿 Available branches:"
git branch -a

echo
echo "📋 Available Operations:"
echo "1. Pull from dev branch"
echo "2. Push to dev branch"
echo "3. Switch to dev branch"
echo "4. Switch to main branch"
echo "5. Create feature branch"
echo "6. Show git status"
echo "7. Commit current changes"
echo "8. Pull from main (merge into dev)"
echo "9. Exit"
echo

read -p "Choose an option (1-9): " choice

case $choice in
    1)
        echo "🔄 Pulling from dev branch..."
        if [ "$CURRENT_BRANCH" != "dev" ]; then
            git checkout dev
        fi
        git pull origin dev
        echo "✅ Successfully pulled from dev branch"
        ;;
    2)
        echo "⬆️ Pushing to dev branch..."
        if [ "$CURRENT_BRANCH" != "dev" ]; then
            echo "❌ Not on dev branch. Switch to dev first."
            exit 1
        fi
        git push origin dev
        echo "✅ Successfully pushed to dev branch"
        ;;
    3)
        echo "🔄 Switching to dev branch..."
        git checkout dev
        echo "✅ Now on dev branch"
        ;;
    4)
        echo "🔄 Switching to main branch..."
        git checkout main
        echo "✅ Now on main branch"
        ;;
    5)
        read -p "Enter feature branch name: " feature_name
        echo "🌿 Creating feature branch: feature/$feature_name"
        git checkout -b "feature/$feature_name"
        echo "✅ Created and switched to feature/$feature_name"
        ;;
    6)
        echo "📊 Git Status:"
        git status
        ;;
    7)
        echo "💾 Committing changes..."
        git status
        echo
        read -p "Enter commit message: " commit_msg
        git add .
        git commit -m "$commit_msg"
        echo "✅ Changes committed"
        ;;
    8)
        echo "🔄 Pulling from main into dev..."
        if [ "$CURRENT_BRANCH" != "dev" ]; then
            git checkout dev
        fi
        git pull origin main
        echo "✅ Successfully merged main into dev"
        ;;
    9)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo
echo "🎉 Operation completed!"
echo "📍 Current branch: $(git branch --show-current)"
