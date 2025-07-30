#!/bin/bash

# Script to resolve merge conflicts in invoice_pdf.html

echo "🔧 Resolving merge conflicts in invoice_pdf.html..."

# Backup the original file
cp /home/azureuser/trendzportal/templates/portal/invoice_pdf.html /home/azureuser/trendzportal/templates/portal/invoice_pdf.html.backup

# Show what the main branch added
echo "📋 Checking what the main branch added..."
git show origin/main:templates/portal/invoice_pdf.html > /tmp/main_version.html
echo "✅ Main branch version saved to /tmp/main_version.html"

# Show what the dev branch has
echo "📋 Checking what the dev branch has..."
git show HEAD:templates/portal/invoice_pdf.html > /tmp/dev_version.html 2>/dev/null || echo "Dev version not available in history"

echo "🔍 Conflicts found at lines:"
grep -n "<<<<<<" /home/azureuser/trendzportal/templates/portal/invoice_pdf.html || echo "No conflicts found"

echo "📝 Manual resolution needed. The main branch likely added:"
echo "- {% load math_filters %} at the top"
echo "- Usage of number_to_words filter in the template"

echo "🚀 You can:"
echo "1. Use the main branch version: git checkout --theirs templates/portal/invoice_pdf.html"
echo "2. Use the dev branch version: git checkout --ours templates/portal/invoice_pdf.html"
echo "3. Manually merge the changes"

echo "💡 I recommend using the main branch version since it has the enhanced features:"
read -p "Use main branch version? (y/n): " choice

if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
    git checkout --theirs templates/portal/invoice_pdf.html
    echo "✅ Using main branch version"
else
    echo "⚠️  Manual resolution needed"
fi
