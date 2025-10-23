# TrendzPortal - Integrated Business Management System

A comprehensive Django-based multi-tenant business management platform designed for modern enterprises. TrendzPortal integrates sales, procurement, inventory, finance, and reporting into a unified, professional system.

## 🚀 **Key Features**

### 📊 **Multi-Module Architecture**
- **Sales & Invoicing**: Complete invoice lifecycle with professional blue theme
- **Procurement**: Supplier management with industrial green theme  
- **Finance**: Financial tracking and reporting with elegant black/gold theme
- **Reports & Analytics**: Data visualization with purple analytics theme
- **Inventory Management**: Product tracking without stock reduction on sales

### 🎨 **Professional Theming**
- **Unique Module Themes**: Each business module has its distinct professional styling
- **Responsive Design**: Bootstrap 5.3.0 with custom CSS enhancements
- **Blue Invoice Theme**: Professional blue interface for all invoice operations
- **Green Procurement Theme**: Industrial-style interface for procurement workflows
- **Dark Finance Theme**: Sophisticated black and gold styling for financial operations
- **Purple Analytics Theme**: Modern purple styling for reports and analytics

### 💼 **Advanced Invoice System**
- **Flexible Pricing**: Toggle between product prices and custom pricing per line item
- **Sales Tracking**: Automatic sales recording without reducing inventory stock
- **Professional UI**: Blue-themed interface with enhanced search functionality
- **Currency Standardization**: Complete QAR (Qatari Riyal) integration
- **Smart Search**: Customer and product search with blue-themed results

### 🏢 **Multi-Tenant Support**
- **Site-Based Separation**: Complete data isolation between tenants
- **Custom Domains**: Support for custom domain mapping per tenant
- **Scalable Architecture**: Django sites framework for enterprise scalability

### 📈 **Intelligent Sales Analytics**
- **Sales Recording**: Automatic tracking of sold items when invoices are paid
- **Inventory Independence**: Sales tracking separate from inventory management
- **Comprehensive Reporting**: Admin interface for sales analysis and reporting
- **Historical Data**: Complete audit trail with customer and product linking

## 🛠 **Quick Start**

### Prerequisites
- Python 3.12+
- Django 5.2.3
- PostgreSQL (recommended) or SQLite for development

### Installation

1. **Clone and Setup**
   ```bash
   cd /home/essyem/tp/trendzportal
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   python3 manage.py migrate
   python3 manage.py createsuperuser
   ```

3. **Multi-Site Configuration**
   ```bash
   python3 manage.py shell
   ```
   ```python
   from django.contrib.sites.models import Site
   Site.objects.get_or_create(domain='portal.almalikaqatar.com', defaults={'name':'Al Malika'})
   ```

4. **Start Development Server**
   ```bash
   python3 manage.py runserver 127.0.0.1:8005
   ```

5. **Access the System**
   - **Main Portal**: http://127.0.0.1:8005/
   - **Admin Interface**: http://127.0.0.1:8005/admin/
   - **Sales Portal**: http://127.0.0.1:8005/invoices/
   - **Procurement**: http://127.0.0.1:8005/procurement/
   - **Finance**: http://127.0.0.1:8005/finance/

## 📁 **Module Overview**

### 🔵 **Sales & Invoicing Module**
- **Professional Blue Theme** with medium-sized navbar
- **Advanced Invoice Management**: Create, edit, track invoice lifecycle
- **Smart Customer Search**: Real-time search with blue-themed results
- **Flexible Product Selection**: Barcode scanning and search functionality
- **Custom Pricing**: Override product prices per invoice line
- **Payment Tracking**: Multiple payment modes including split payments

### 🟢 **Procurement Module**  
- **Industrial Green Theme** with extra-large navbar
- **Supplier Management**: Complete supplier lifecycle management
- **Purchase Order System**: Create and track purchase orders
- **Payment Processing**: Handle supplier payments and tracking
- **Integration**: Seamless integration with inventory and finance

### ⚫ **Finance Module**
- **Elegant Black/Gold Theme** with large navbar
- **Transaction Management**: Income and expense tracking
- **Daily Revenue Reporting**: Comprehensive revenue analytics
- **Financial Dashboard**: Real-time financial metrics
- **QAR Currency**: Complete Qatari Riyal integration

### 🟣 **Reports & Analytics**
- **Purple Analytics Theme** for data visualization
- **Sales Reports**: Detailed sales performance analytics  
- **Inventory Reports**: Stock levels and movement tracking
- **Financial Reports**: Revenue, expenses, and profitability analysis
- **Customer Analytics**: Customer behavior and sales patterns

## 💡 **Advanced Features**

### 🎯 **Smart Sales Tracking**
- **SoldItem Model**: Tracks sales without reducing inventory stock
- **Automatic Recording**: Django signals create sales records when invoices are paid
- **Separate Analytics**: Inventory management separate from sales reporting
- **Historical Tracking**: Complete audit trail with product and customer linking

### 🔧 **Flexible Pricing System**
- **Price Override Controls**: Checkbox to toggle between product and custom pricing
- **Per-Line Flexibility**: Each invoice line can use different pricing approaches
- **Real-time Updates**: JavaScript handles price changes seamlessly
- **Currency Consistency**: QAR formatting throughout the system

### 📊 **Professional UI/UX**
- **Module-Specific Themes**: Each business area has unique professional styling
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Enhanced Navigation**: Large, themed navbars for easy module identification
- **Consistent Branding**: Professional color schemes and typography

## 🗃 **Database Architecture**

### Core Models
- **Customer**: Multi-tenant customer management
- **Product**: Inventory with category organization
- **Invoice/InvoiceItem**: Complete invoicing system
- **SoldItem**: Sales tracking without stock reduction
- **Supplier**: Procurement supplier management
- **PurchaseOrder**: Procurement order management

### Multi-Tenant Design
- **Site-Based Separation**: Django sites framework
- **Data Isolation**: Complete separation between tenants
- **Scalable**: Supports unlimited tenants

## 🚀 **Deployment**

### Development
```bash
python3 manage.py runserver 127.0.0.1:8005
```

### Production
- **Static Files**: `python3 manage.py collectstatic`
- **Migrations**: `python3 manage.py migrate`
- **Web Server**: Nginx + Gunicorn recommended
- **Database**: PostgreSQL for production

## 📝 **Recent Enhancements**

### 🎨 **Complete Theme Overhaul**
- **Four Unique Themes**: Finance (black/gold), Procurement (green), Invoices (blue), Reports (purple)
- **Enhanced Navigation**: Large, themed navbars for easy module identification
- **Professional Styling**: Custom CSS with gradients, shadows, and animations

### 💰 **Currency Standardization**
- **QAR Integration**: Complete conversion from USD to Qatari Riyal
- **Consistent Formatting**: QAR currency symbols throughout all modules
- **Admin Updates**: All admin interfaces use QAR formatting

### 🔍 **Advanced Search System**
- **Blue-Themed Results**: Customer and product search with professional styling
- **Real-time Search**: Ajax-powered search with instant results
- **Enhanced UX**: Hover effects and smooth animations

### 📈 **Sales Intelligence**
- **Automatic Tracking**: Sales recorded when invoices marked as paid
- **Inventory Independence**: Stock levels separate from sales tracking
- **Comprehensive Reporting**: Admin interface for sales analytics

## 🔗 **Key URLs**

- **Dashboard**: `/` - Main application dashboard
- **Invoices**: `/invoices/` - Sales and invoicing module
- **Procurement**: `/procurement/` - Supplier and purchase management  
- **Finance**: `/finance/` - Financial management and reporting
- **Admin**: `/admin/` - Django admin interface
- **API Endpoints**: `/ajax/` - Customer and product search APIs

## 🤝 **Contributing**

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

## 📞 **Support & Contact**

- **Repository**: https://github.com/Trendz-Trading-and-Services/salesportal
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Documentation**: Comprehensive guides in `/docs/` directory

## 📄 **License**

This project is proprietary software developed for Trendz Trading and Services. All rights reserved.

---

**TrendzPortal** - Empowering businesses with integrated management solutions. 🚀