# Azure Staging Instance Git Pull & Deployment Guide

## 🎯 **Overview**
This guide provides step-by-step instructions to pull the latest changes from GitHub and overwrite existing changes in your Azure staging instance.

## 📋 **Prerequisites**
- SSH/RDP access to your Azure staging instance
- Git installed on the staging server
- Appropriate permissions to modify files
- Python virtual environment setup

---

## 🚀 **Step-by-Step Deployment Process**

### **Step 1: Connect to Azure Staging Instance**
```bash
# SSH into your Azure staging instance
ssh username@your-staging-server.azurewebsites.net
# OR use Azure Cloud Shell / RDP if Windows
```

### **Step 2: Navigate to Project Directory**
```bash
# Navigate to your project directory (adjust path as needed)
cd /home/site/wwwroot/
# OR for Linux App Service:
cd /var/www/html/trendzportal/
# OR wherever your project is located
```

### **Step 3: Check Current Git Status**
```bash
# Check current branch and status
git status
git branch -a
git remote -v
```

### **Step 4: Backup Current State (Optional but Recommended)**
```bash
# Create a backup of current changes
git stash push -m "Backup before pull $(date)"
# OR create a backup branch
git checkout -b backup-$(date +%Y%m%d-%H%M%S)
git add .
git commit -m "Backup before deployment"
git checkout main
```

### **Step 5: Force Pull Latest Changes**
```bash
# Method 1: Hard reset (OVERWRITES local changes)
git fetch origin
git reset --hard origin/main
git clean -fd

# Method 2: Alternative approach
git fetch origin
git checkout main
git reset --hard HEAD
git merge origin/main
```

### **Step 6: Verify Latest Changes**
```bash
# Check that you have the latest commit
git log --oneline -5
# Should show: ff7b616 Fix finance module and PDF invoice formatting

# Verify files are updated
ls -la templates/portal/invoice_pdf.html
ls -la finance/forms.py
```

### **Step 7: Update Python Dependencies**
```bash
# Activate virtual environment (adjust path as needed)
source venv/bin/activate
# OR
source .venv/bin/activate

# Install/update dependencies
pip install -r requirements-frozen.txt
# OR if you prefer the main requirements file:
pip install -r requirements.txt
```

### **Step 8: Django Management Commands**
```bash
# Collect static files
python manage.py collectstatic --noinput

# Run database migrations (if any)
python manage.py migrate

# Check for any issues
python manage.py check --deploy
```

### **Step 9: Restart Application Services**
```bash
# For Linux App Service
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# OR for Azure App Service (if using custom startup)
# The app will restart automatically after file changes

# OR manually restart via Azure Portal:
# Go to Azure Portal > App Service > Restart
```

### **Step 10: Verify Deployment**
```bash
# Check application logs
tail -f /var/log/django.log
# OR
tail -f logs/django.log

# Test the application
curl -I http://your-staging-url.azurewebsites.net/
```

---

## 🔧 **Alternative: One-Command Deployment Script**

Create a deployment script for easier future updates:

```bash
# Create deployment script
cat > deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Backup current state
echo "📦 Creating backup..."
git stash push -m "Auto-backup $(date)"

# Pull latest changes
echo "⬇️ Pulling latest changes..."
git fetch origin
git reset --hard origin/main
git clean -fd

# Update dependencies
echo "📚 Updating dependencies..."
source .venv/bin/activate
pip install -r requirements-frozen.txt

# Django management
echo "🔧 Running Django management commands..."
python manage.py collectstatic --noinput
python manage.py migrate

# Restart services (adjust as needed)
echo "🔄 Restarting services..."
sudo systemctl restart gunicorn 2>/dev/null || echo "Gunicorn restart skipped"
sudo systemctl restart nginx 2>/dev/null || echo "Nginx restart skipped"

echo "✅ Deployment completed successfully!"
echo "📋 Current commit: $(git log --oneline -1)"
EOF

# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

---

## 🚨 **Troubleshooting Common Issues**

### **Issue 1: Permission Denied**
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod -R 755 .
```

### **Issue 2: Virtual Environment Not Found**
```bash
# Create new virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-frozen.txt
```

### **Issue 3: Database Connection Issues**
```bash
# Check database settings
python manage.py shell
>>> from django.conf import settings
>>> print(settings.DATABASES)

# Test database connection
python manage.py dbshell
```

### **Issue 4: Static Files Not Loading**
```bash
# Force collect static files
python manage.py collectstatic --clear --noinput
# Check static files directory
ls -la staticfiles/
```

### **Issue 5: Application Not Restarting**
```bash
# Force restart via Azure CLI (if available)
az webapp restart --name your-app-name --resource-group your-resource-group

# OR touch a file to trigger restart
touch web.config
# OR
touch requirements.txt
```

---

## 📊 **Verification Checklist**

After deployment, verify these components:

- [ ] **Homepage loads correctly**
- [ ] **Finance module transactions work** (http://your-staging-url/finance/transactions/)
- [ ] **PDF invoice generation works** (http://your-staging-url/invoices/95/pdf/)
- [ ] **Footer displays properly** in PDFs
- [ ] **Transaction totals show correct values** (not concatenated strings)
- [ ] **TrendzApps appears bold** in header
- [ ] **Affiliation text appears** in footer
- [ ] **All static files load** (CSS, JS, images)
- [ ] **Database operations work** correctly

---

## 🔗 **Quick Reference Commands**

```bash
# Quick status check
git log --oneline -1 && git status

# Force pull latest
git fetch origin && git reset --hard origin/main

# Quick restart (adjust for your setup)
sudo systemctl restart gunicorn nginx

# View recent logs
tail -20 logs/django.log
```

---

## 📞 **Support Information**

- **Repository:** https://github.com/Trendz-Trading-and-Services/salesportal.git
- **Latest Commit:** ff7b616 - Fix finance module and PDF invoice formatting
- **Branch:** main
- **Python Version:** 3.12.3
- **Django Version:** 5.2.3

For any issues during deployment, check the logs and ensure all prerequisites are met.