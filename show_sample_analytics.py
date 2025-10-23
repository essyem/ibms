#!/usr/bin/env python3
"""
Display sample daily revenue analytics and generate sample PDFs
"""

import os
import sys
import django
from datetime import date
from decimal import Decimal

# Setup Django environment
sys.path.append('/home/essyem/tp/trendzportal')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
django.setup()

from finance.models import DailyRevenue

def display_analytics():
    """Display detailed analytics for September 2025 sample data"""
    
    entries = DailyRevenue.objects.filter(date__month=9, date__year=2025).order_by('date')
    
    if not entries:
        print("❌ No data found for September 2025")
        return
    
    print("📈 DAILY REVENUE ANALYTICS - SEPTEMBER 2025")
    print("=" * 60)
    
    # Weekly breakdown
    weeks = {}
    for entry in entries:
        week_num = entry.date.isocalendar()[1]  # Get ISO week number
        if week_num not in weeks:
            weeks[week_num] = []
        weeks[week_num].append(entry)
    
    print("\n📅 WEEKLY BREAKDOWN:")
    for week_num in sorted(weeks.keys()):
        week_entries = weeks[week_num]
        week_revenue = sum(e.daily_revenue for e in week_entries)
        week_cash = sum(e.daily_cash_sales for e in week_entries)
        week_pos = sum(e.daily_pos_sales for e in week_entries)
        week_service = sum(e.daily_service_revenue for e in week_entries)
        week_purchase = sum(e.daily_purchase for e in week_entries)
        
        print(f"  Week {week_num}: {len(week_entries)} days, Revenue: ${week_revenue:,.2f}")
        print(f"    Cash: ${week_cash:,.2f}, POS: ${week_pos:,.2f}, Service: ${week_service:,.2f}, Purchase: ${week_purchase:,.2f}")
    
    # Day of week analysis
    print("\n📊 DAY OF WEEK ANALYSIS:")
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_data = {i: [] for i in range(7)}
    
    for entry in entries:
        dow = entry.date.weekday()
        dow_data[dow].append(entry)
    
    for dow in range(7):
        if dow_data[dow]:
            avg_revenue = sum(e.daily_revenue for e in dow_data[dow]) / len(dow_data[dow])
            count = len(dow_data[dow])
            print(f"  {days_of_week[dow]}: {count} days, Avg Revenue: ${avg_revenue:,.2f}")
    
    # Payment method breakdown
    print("\n💳 PAYMENT METHOD BREAKDOWN:")
    total_cash = sum(e.daily_cash_sales for e in entries)
    total_pos = sum(e.daily_pos_sales for e in entries)
    total_service = sum(e.daily_service_revenue for e in entries)
    total_sales = total_cash + total_pos + total_service
    
    if total_sales > 0:
        cash_pct = (total_cash / total_sales) * 100
        pos_pct = (total_pos / total_sales) * 100
        service_pct = (total_service / total_sales) * 100
        
        print(f"  Cash Sales: ${total_cash:,.2f} ({cash_pct:.1f}%)")
        print(f"  POS Sales: ${total_pos:,.2f} ({pos_pct:.1f}%)")
        print(f"  Service Revenue: ${total_service:,.2f} ({service_pct:.1f}%)")
    
    # Top performing days
    print("\n🏆 TOP 5 PERFORMING DAYS:")
    top_days = sorted(entries, key=lambda x: x.daily_revenue, reverse=True)[:5]
    for i, entry in enumerate(top_days, 1):
        day_name = entry.date.strftime('%A')
        print(f"  {i}. {entry.date} ({day_name}): ${entry.daily_revenue:,.2f}")
        print(f"     Cash: ${entry.daily_cash_sales}, POS: ${entry.daily_pos_sales}, Service: ${entry.daily_service_revenue}, Purchase: ${entry.daily_purchase}")
    
    # Monthly trends
    print("\n📈 MONTHLY TRENDS:")
    total_revenue = sum(e.daily_revenue for e in entries)
    total_purchases = sum(e.daily_purchase for e in entries)
    profit_margin = ((total_revenue - total_purchases) / total_revenue * 100) if total_revenue > 0 else 0
    
    print(f"  Total Days: {len(entries)}")
    print(f"  Total Revenue: ${total_revenue:,.2f}")
    print(f"  Total Purchases: ${total_purchases:,.2f}")
    print(f"  Net Profit: ${total_revenue - total_purchases:,.2f}")
    print(f"  Profit Margin: {profit_margin:.1f}%")
    print(f"  Average Daily Revenue: ${total_revenue / len(entries):,.2f}")
    
    # Show sample entries for different scenarios
    print("\n📋 SAMPLE DAILY ENTRIES:")
    print("─" * 60)
    
    # Show a few specific dates as examples
    sample_dates = [
        date(2025, 9, 6),   # Weekend day
        date(2025, 9, 15),  # Weekday
        date(2025, 9, 28),  # Best day
        date(2025, 9, 8),   # Worst day
    ]
    
    for sample_date in sample_dates:
        try:
            entry = DailyRevenue.objects.get(date=sample_date)
            day_name = entry.date.strftime('%A')
            print(f"\n📅 {entry.date} ({day_name}):")
            print(f"   Cash Sales: ${entry.daily_cash_sales:,.2f}")
            print(f"   POS Sales: ${entry.daily_pos_sales:,.2f}")
            print(f"   Service Revenue: ${entry.daily_service_revenue:,.2f}")
            print(f"   Daily Purchase: ${entry.daily_purchase:,.2f}")
            print(f"   ─────────────────────────────")
            print(f"   DAILY REVENUE: ${entry.daily_revenue:,.2f}")
            
            if entry.daily_revenue > 0:
                print(f"   📈 Profitable Day (+${entry.daily_revenue:,.2f})")
            else:
                print(f"   📉 Loss Day (${entry.daily_revenue:,.2f})")
            
            profit_margin = ((entry.daily_revenue / (entry.daily_cash_sales + entry.daily_pos_sales + entry.daily_service_revenue)) * 100) if (entry.daily_cash_sales + entry.daily_pos_sales + entry.daily_service_revenue) > 0 else 0
            print(f"   💰 Profit Margin: {profit_margin:.1f}%")
            
        except DailyRevenue.DoesNotExist:
            print(f"❌ No data for {sample_date}")

if __name__ == '__main__':
    display_analytics()
