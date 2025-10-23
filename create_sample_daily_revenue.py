#!/usr/bin/env python3
"""
Create sample daily revenue data for September 2025
This script generates realistic daily revenue entries to demonstrate the system
"""

import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal
import random

# Setup Django environment
sys.path.append('/home/essyem/tp/trendzportal')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
django.setup()

from django.contrib.auth.models import User
from finance.models import DailyRevenue

def create_sample_data():
    """Create sample daily revenue data for September 2025"""
    
    # Get or create a user for the entries
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@trendzportal.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        user.set_password('admin123')
        user.save()
        print(f"Created admin user: {user.username}")
    else:
        print(f"Using existing user: {user.username}")

    # Clear existing data for September 2025
    start_date = date(2025, 9, 1)
    end_date = date(2025, 9, 30)
    DailyRevenue.objects.filter(date__range=[start_date, end_date]).delete()
    print("Cleared existing September 2025 data")

    # Sample data for September 2025 (30 days)
    sample_entries = []
    
    for day in range(1, 31):  # September has 30 days
        entry_date = date(2025, 9, day)
        day_of_week = entry_date.weekday()  # 0=Monday, 6=Sunday
        
        # Adjust sales based on day of week (weekends typically higher)
        base_cash = 2500 if day_of_week < 5 else 3500  # Higher on weekends
        base_pos = 1800 if day_of_week < 5 else 2800
        base_service = 800 if day_of_week < 5 else 1200
        base_purchase = 1500 if day_of_week < 5 else 2000
        
        # Add some random variation (±20%)
        cash_variation = random.uniform(0.8, 1.2)
        pos_variation = random.uniform(0.8, 1.2)
        service_variation = random.uniform(0.8, 1.2)
        purchase_variation = random.uniform(0.8, 1.2)
        
        daily_cash_sales = Decimal(str(round(base_cash * cash_variation, 2)))
        daily_pos_sales = Decimal(str(round(base_pos * pos_variation, 2)))
        daily_service_revenue = Decimal(str(round(base_service * service_variation, 2)))
        daily_purchase = Decimal(str(round(base_purchase * purchase_variation, 2)))
        
        # Create the entry
        entry = DailyRevenue.objects.create(
            date=entry_date,
            daily_cash_sales=daily_cash_sales,
            daily_pos_sales=daily_pos_sales,
            daily_service_revenue=daily_service_revenue,
            daily_purchase=daily_purchase,
            entered_by=user
        )
        
        sample_entries.append(entry)
        
        # Add some print tracking for random entries
        if random.random() < 0.3:  # 30% chance of being printed
            entry.mark_printed(user)
        
        print(f"Created entry for {entry_date}: Cash: ${daily_cash_sales}, POS: ${daily_pos_sales}, Service: ${daily_service_revenue}, Purchase: ${daily_purchase}, Revenue: ${entry.daily_revenue}")

    print(f"\n✅ Created {len(sample_entries)} daily revenue entries for September 2025")
    
    # Calculate and display summary statistics
    total_cash = sum(entry.daily_cash_sales for entry in sample_entries)
    total_pos = sum(entry.daily_pos_sales for entry in sample_entries)
    total_service = sum(entry.daily_service_revenue for entry in sample_entries)
    total_purchases = sum(entry.daily_purchase for entry in sample_entries)
    total_revenue = sum(entry.daily_revenue for entry in sample_entries)
    
    print(f"\n📊 SEPTEMBER 2025 SUMMARY:")
    print(f"Total Cash Sales: ${total_cash:,.2f}")
    print(f"Total POS Sales: ${total_pos:,.2f}")
    print(f"Total Service Revenue: ${total_service:,.2f}")
    print(f"Total Purchases: ${total_purchases:,.2f}")
    print(f"Total Revenue: ${total_revenue:,.2f}")
    print(f"Average Daily Revenue: ${total_revenue/30:,.2f}")
    
    # Show profit/loss breakdown
    profitable_days = len([e for e in sample_entries if e.daily_revenue > 0])
    loss_days = 30 - profitable_days
    
    print(f"\n💰 PERFORMANCE BREAKDOWN:")
    print(f"Profitable Days: {profitable_days}")
    print(f"Loss Days: {loss_days}")
    print(f"Profit Rate: {(profitable_days/30)*100:.1f}%")
    
    # Show best and worst performing days
    best_day = max(sample_entries, key=lambda x: x.daily_revenue)
    worst_day = min(sample_entries, key=lambda x: x.daily_revenue)
    
    print(f"\n🏆 BEST PERFORMING DAY:")
    print(f"Date: {best_day.date}")
    print(f"Revenue: ${best_day.daily_revenue:,.2f}")
    print(f"Breakdown: Cash: ${best_day.daily_cash_sales}, POS: ${best_day.daily_pos_sales}, Service: ${best_day.daily_service_revenue}, Purchase: ${best_day.daily_purchase}")
    
    print(f"\n📉 WORST PERFORMING DAY:")
    print(f"Date: {worst_day.date}")
    print(f"Revenue: ${worst_day.daily_revenue:,.2f}")
    print(f"Breakdown: Cash: ${worst_day.daily_cash_sales}, POS: ${worst_day.daily_pos_sales}, Service: ${worst_day.daily_service_revenue}, Purchase: ${worst_day.daily_purchase}")

if __name__ == '__main__':
    print("Creating sample daily revenue data for September 2025...")
    create_sample_data()
    print("\n🎉 Sample data creation completed successfully!")
    print("You can now visit the Daily Revenue Dashboard to see the data.")
