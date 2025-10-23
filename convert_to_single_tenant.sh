#!/bin/bash
# Single-Tenant Migration Script for Trendz Portal

echo "🔄 Converting to Single-Tenant Architecture"

# Step 1: Backup current templates
echo "📦 Creating backup..."
cp -r templates/ templates_backup_$(date +%Y%m%d_%H%M%S)/

# Step 2: Consolidate templates
echo "🔗 Consolidating templates..."
# Move site-specific portal templates to main template directory
cp -r templates/sites/portal/portal/* templates/portal/ 2>/dev/null || true

# Step 3: Remove multi-tenant structure
echo "🗑️ Removing multi-tenant directories..."
# rm -rf templates/sites/

# Step 4: Update settings
echo "⚙️ Settings need manual update:"
echo "- Remove 'templates/sites' from TEMPLATES['DIRS']"
echo "- Remove site_context from context_processors"
echo "- Simplify template paths"

echo "✅ Single-tenant conversion ready!"
echo "📋 Manual steps needed:"
echo "   1. Update settings.py"
echo "   2. Remove Sites framework if not needed"
echo "   3. Test all templates"
echo "   4. Update any hardcoded site references"
