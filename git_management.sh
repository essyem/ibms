#!/bin/bash

# Git Management Script for TrendzPortal
# This script helps manage your git repository with many modified files

set -e

echo "🔧 TrendzPortal Git Management"
echo "=============================="
echo

# Check current status
echo "📊 Current Git Status:"
echo "- Branch: $(git branch --show-current)"
echo "- Remote: $(git remote get-url origin)"
echo "- Modified files: $(git status --porcelain | grep -c "^ M" || echo "0")"
echo "- Untracked files: $(git status --porcelain | grep -c "^??" || echo "0")"
echo

# Function to create gitignore for temporary files
create_gitignore() {
    echo "📝 Creating/updating .gitignore..."
    
    cat >> .gitignore << 'EOF'

# Backup and temporary files
*.bak
*.backup
*_backup.*
*_bak.*
*_clean.*
*.pdf
*.dump
*.gz
*.tar.gz

# Test files
test_*.py
test_*.pdf
test_*.html

# Logs and debug files
logs/
debug_*.py
*debug*.py

# Media uploads
media/products/
media/uploads/

# Static files (should be regenerated)
staticfiles/
static/collected/

# Development files
.env
.env.local
.env.development
.env.test

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# Django specific
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Temporary directories
tmp/
temp/
EOF
    
    echo "✅ .gitignore updated"
}

# Function to stash current changes
stash_changes() {
    echo "📦 Stashing current changes..."
    git add .
    git stash push -m "Stash before pulling from dev - $(date)"
    echo "✅ Changes stashed successfully"
}

# Function to create dev branch
create_dev_branch() {
    echo "🌿 Creating dev branch..."
    
    # Create dev branch from current main
    git checkout -b dev
    
    # Push dev branch to remote
    git push -u origin dev
    
    echo "✅ Dev branch created and pushed to remote"
}

# Function to commit current changes to dev
commit_to_dev() {
    echo "💾 Committing changes to dev branch..."
    
    # Add all changes
    git add .
    
    # Create commit message
    COMMIT_MSG="Development changes - $(date '+%Y-%m-%d %H:%M:%S')

- Updated portal, finance, procurement modules
- Added barcode functionality
- Updated templates and static files
- Added testing files
- Enhanced admin interface"

    git commit -m "$COMMIT_MSG"
    
    echo "✅ Changes committed to dev branch"
}

# Function to pull latest changes
pull_changes() {
    echo "⬇️ Pulling latest changes..."
    
    # Fetch all remote branches
    git fetch origin
    
    # Pull from main if on main, or dev if on dev
    CURRENT_BRANCH=$(git branch --show-current)
    git pull origin "$CURRENT_BRANCH"
    
    echo "✅ Latest changes pulled"
}

# Function to clean up temporary files
cleanup_temp_files() {
    echo "🧹 Cleaning up temporary files..."
    
    # Remove backup files
    find . -name "*.bak" -type f -delete 2>/dev/null || true
    find . -name "*.backup" -type f -delete 2>/dev/null || true
    find . -name "*_backup.*" -type f -delete 2>/dev/null || true
    find . -name "*_bak.*" -type f -delete 2>/dev/null || true
    find . -name "*_clean.*" -type f -delete 2>/dev/null || true
    
    # Remove test files
    find . -name "test_*.py" -not -path "./portal/tests/*" -not -path "./*/tests/*" -delete 2>/dev/null || true
    find . -name "test_*.pdf" -delete 2>/dev/null || true
    
    # Remove debug files
    find . -name "*debug*.py" -delete 2>/dev/null || true
    
    echo "✅ Temporary files cleaned up"
}

# Main menu
show_menu() {
    echo "📋 What would you like to do?"
    echo "1. Create .gitignore file"
    echo "2. Clean up temporary files"
    echo "3. Create dev branch"
    echo "4. Stash changes and pull"
    echo "5. Commit changes to dev"
    echo "6. Pull latest changes"
    echo "7. Full workflow (recommended)"
    echo "8. Exit"
    echo
    read -p "Enter your choice (1-8): " choice
}

# Full workflow function
full_workflow() {
    echo "🚀 Starting full workflow..."
    
    create_gitignore
    cleanup_temp_files
    
    # Check if dev branch exists
    if git branch -r | grep -q "origin/dev"; then
        echo "📥 Dev branch exists, switching to it..."
        git checkout dev 2>/dev/null || git checkout -b dev
    else
        echo "🌿 Creating new dev branch..."
        create_dev_branch
    fi
    
    commit_to_dev
    pull_changes
    
    echo "🎉 Full workflow completed!"
    echo "📋 Summary:"
    echo "- Created/updated .gitignore"
    echo "- Cleaned temporary files"
    echo "- Committed changes to dev branch"
    echo "- Pulled latest changes"
}

# Main execution
main() {
    # Check if we're in a git repository
    if ! git rev-parse --is-inside-work-tree &>/dev/null; then
        echo "❌ Not in a git repository!"
        exit 1
    fi
    
    while true; do
        show_menu
        case $choice in
            1)
                create_gitignore
                ;;
            2)
                cleanup_temp_files
                ;;
            3)
                create_dev_branch
                ;;
            4)
                stash_changes
                pull_changes
                ;;
            5)
                commit_to_dev
                ;;
            6)
                pull_changes
                ;;
            7)
                full_workflow
                break
                ;;
            8)
                echo "👋 Goodbye!"
                break
                ;;
            *)
                echo "❌ Invalid choice. Please try again."
                ;;
        esac
        echo
        read -p "Press Enter to continue..."
        echo
    done
}

# Run main function
main
