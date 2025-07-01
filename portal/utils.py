# portal/utils.py
import arabic_reshaper
from bidi.algorithm import get_display
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from django.conf import settings


def process_arabic_text(text):
    """
    Process Arabic text to be displayed correctly in PDFs
    """
    if not text:
        return ""
    
    # Reshape Arabic text
    reshaped_text = arabic_reshaper.reshape(str(text))
    
    # Apply bidirectional algorithm
    display_text = get_display(reshaped_text)
    
    return display_text


def register_arabic_fonts():
    """
    Register Arabic fonts for use in ReportLab
    """
    fonts_registered = False
    
    # Define font paths to try
    font_paths = [
        '/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf',
        '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',
        '/usr/share/fonts/truetype/fonts-arabeyes/ae_Arab.ttf',
        '/usr/share/fonts/truetype/fonts-kacst/KacstOne.ttf',
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
                fonts_registered = True
                break
            except Exception as e:
                continue
    
    return fonts_registered


def create_arabic_paragraph_style():
    """
    Create a paragraph style suitable for Arabic text
    """
    styles = getSampleStyleSheet()
    
    arabic_style = ParagraphStyle(
        'ArabicStyle',
        parent=styles['Normal'],
        fontName='ArabicFont',
        fontSize=12,
        leading=16,
        alignment=2,  # Right alignment
        rightIndent=0,
        leftIndent=0,
        spaceAfter=6,
    )
    
    return arabic_style


def create_english_paragraph_style():
    """
    Create a paragraph style suitable for English text
    """
    styles = getSampleStyleSheet()
    
    english_style = ParagraphStyle(
        'EnglishStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        alignment=0,  # Left alignment
        rightIndent=0,
        leftIndent=0,
        spaceAfter=6,
    )
    
    return english_style


def prepare_bilingual_text(english_text, arabic_text=None):
    """
    Prepare bilingual text for PDF display
    """
    if arabic_text:
        processed_arabic = process_arabic_text(arabic_text)
        return f"{english_text} / {processed_arabic}"
    return english_text
