from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def build_monthly_report_pdf(title: str, start_date: date, end_date: date, total_cases: int, total_grafts: int, personnel_totals: dict[str, Decimal], total_bonus: Decimal) -> bytes:
    buffer = BytesIO()
    pdfmetrics.registerFont(TTFont("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("DejaVuSans", 13)
    c.drawString(50, 800, title)
    c.setFont("DejaVuSans", 11)
    c.drawString(50, 780, f"Tarih aralığı: {start_date} - {end_date}")
    c.drawString(50, 760, f"Oluşturulma: {datetime.utcnow().isoformat()}")
    c.drawString(50, 740, f"Vaka sayısı: {total_cases}")
    c.drawString(50, 720, f"Toplam greft: {total_grafts}")

    y = 700
    c.drawString(50, y, "Personel bazlı primler:")
    y -= 20
    for name, amount in personnel_totals.items():
        c.drawString(60, y, f"- {name}: {amount} USD")
        y -= 18

    c.drawString(50, y - 8, f"Genel toplam: {total_bonus} USD")
    c.showPage()
    c.save()
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data
