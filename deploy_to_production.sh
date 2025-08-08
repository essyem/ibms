#!/bin/bash
# 🚀 TrendzPortal Production Deployment Script
# Run this script on your production server

echo "🚀 Starting TrendzPortal Production Deployment..."
echo "=================================================="

# 1. Navigate to production directory
cd /path/to/your/production/trendzportal
echo "📁 Current directory: $(pwd)"

# 2. Backup current state
echo "💾 Creating backup..."
sudo cp -r . ../trendzportal_backup_$(date +%Y%m%d_%H%M%S)

# 3. Pull latest changes from dev branch
echo "📥 Pulling latest changes from GitHub..."
git fetch origin
git checkout dev
git pull origin dev

# 4. Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate  # or wherever your venv is located

# 5. Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# 6. Run database migrations
echo "🗃️ Running database migrations..."
python manage.py migrate

# 7. Collect static files
echo "📱 Collecting static files..."
python manage.py collectstatic --noinput

# 8. Test the deployment
echo "🧪 Testing deployment..."
python manage.py check --deploy

# 9. Restart application server
echo "🔄 Restarting application server..."
# For systemd service:
# sudo systemctl restart trendzportal

# For supervisor:
# sudo supervisorctl restart trendzportal

# For gunicorn/uwsgi:
# sudo pkill -HUP gunicorn
# sudo systemctl restart nginx

echo "✅ Deployment completed successfully!"
echo "🌐 Your application should now be updated with:"
echo "   - Fixed invoice number generation (YYYYMMDDNN format)"
echo "   - Proper status handling (draft/paid/sent/cancelled)"
echo "   - Enhanced form validation"
echo "   - Improved error handling"

echo ""
echo "🔍 Next steps:"
echo "1. Test invoice creation functionality"
echo "2. Verify invoice numbers are generating correctly"
echo "3. Check that invoice statuses are preserved"
echo "4. Monitor logs for any issues"

echo ""
echo "📞 Need help? Check the logs at:"
echo "   - Application logs: logs/django.log"
echo "   - Error logs: logs/django_error.log"
echo "   - Web server logs: /var/log/nginx/ (if using nginx)"
