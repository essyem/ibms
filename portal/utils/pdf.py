# utils/pdf.py
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import lightgrey
import qrcode

def generate_invoice_pdf(invoice, watermark_text="CONFIDENTIAL", download=False):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Watermark
    c.setFillColor(lightgrey)
    c.setFont("Helvetica", 60)
    c.saveState()
    c.translate(width/2, height/3)
    c.rotate(45)
    c.drawCentredString(0, 0, watermark_text)
    c.restoreState()
    
    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=4,
    )
    payment_info = f"INVOICE:{invoice.invoice_number}\nAMOUNT:{invoice.total}\nDUE:{invoice.due_date}"
    qr.add_data(payment_info)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Add QR code to PDF
    qr_img_reader = ImageReader(qr_buffer)
    c.drawImage(qr_img_reader, width-150, 100, 100, 100)
    
    # Add payment instructions near QR
    c.setFont("Helvetica", 10)
    c.drawString(width-150, 90, "Scan to view payment details")
    
    # Add your regular invoice content here
    # ... [your existing invoice content generation code]
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer