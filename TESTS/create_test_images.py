"""
Test-Bilder und PDF-Dateien generieren
========================================

Erstellt realistische Test-Dateien für den Precheck:
- zaehler.jpg (800x600, Zählerschrank-Mockup)
- hausanschluss.jpg (800x600, Hausanschluss-Mockup)
- montageort.jpg (800x600, Montageort-Mockup)
- kabelwege.pdf (Mini-PDF mit Text)

Verwendung:
    python create_test_images.py
"""

import os
from pathlib import Path
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  Pillow nicht installiert. Installiere mit: pip install Pillow")

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️  ReportLab nicht installiert. Installiere mit: pip install reportlab")


BILDER_DIR = Path(__file__).parent / "Bilder"


def create_test_image(filename, title, color=(100, 150, 200)):
    """
    Erstellt ein Test-Bild mit Titel und Farbe

    Args:
        filename: Dateiname (z.B. "zaehler.jpg")
        title: Titel-Text auf dem Bild
        color: RGB-Farbe des Hintergrunds
    """
    if not PIL_AVAILABLE:
        print(f"❌ Kann {filename} nicht erstellen (Pillow fehlt)")
        return False

    # Bild erstellen
    width, height = 800, 600
    image = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(image)

    # Versuche eine bessere Schrift zu laden
    try:
        font_title = ImageFont.truetype("arial.ttf", 48)
        font_subtitle = ImageFont.truetype("arial.ttf", 24)
    except:
        # Fallback auf Default-Font
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()

    # Titel zeichnen
    draw.text(
        (width // 2, height // 3),
        title,
        fill='white',
        font=font_title,
        anchor='mm'
    )

    # Untertitel
    draw.text(
        (width // 2, height // 2),
        "TEST-BILD",
        fill='white',
        font=font_subtitle,
        anchor='mm'
    )

    # Dateiname
    draw.text(
        (width // 2, height * 2 // 3),
        filename,
        fill='lightgray',
        font=font_subtitle,
        anchor='mm'
    )

    # Rahmen
    draw.rectangle([(10, 10), (width-10, height-10)], outline='white', width=3)

    # Speichern
    file_path = BILDER_DIR / filename
    image.save(file_path, 'JPEG', quality=85)
    file_size_mb = file_path.stat().st_size / (1024 * 1024)

    print(f"   ✅ {filename} erstellt ({file_size_mb:.2f} MB)")
    return True


def create_test_pdf(filename="kabelwege.pdf"):
    """Erstellt ein einfaches Test-PDF"""

    if not REPORTLAB_AVAILABLE:
        print(f"❌ Kann {filename} nicht erstellen (ReportLab fehlt)")
        # Erstelle minimales PDF manuell
        return create_minimal_pdf(filename)

    file_path = BILDER_DIR / filename
    c = canvas.Canvas(str(file_path), pagesize=A4)

    # Titel
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(300, 750, "Kabelwege - Test-Dokument")

    # Inhalt
    c.setFont("Helvetica", 12)
    y = 700
    lines = [
        "Dies ist ein Test-PDF für den Precheck-Upload.",
        "",
        "Kabellängen:",
        "• Zählerplatz → Wechselrichter: 12.5 m",
        "• Wechselrichter → Wallbox: 25 m",
        "• Gesamt: 37.5 m",
        "",
        "Kabeltypen:",
        "• NYM-J 5x6 mm² (Hauptleitung)",
        "• NYM-J 5x2.5 mm² (Wallbox)",
        "",
        "Verlegeart: Unterputz in Installationsrohr",
        "",
        f"Erstellt: {Path(__file__).name}",
    ]

    for line in lines:
        c.drawString(50, y, line)
        y -= 20

    # Rahmen
    c.rect(30, 30, 550, 800, stroke=1, fill=0)

    c.save()

    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"   ✅ {filename} erstellt ({file_size_mb:.2f} MB)")
    return True


def create_minimal_pdf(filename="kabelwege.pdf"):
    """Erstellt ein minimales PDF ohne ReportLab"""
    file_path = BILDER_DIR / filename

    # Minimaler PDF-Inhalt
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources 4 0 R /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >>
endobj
5 0 obj
<< /Length 100 >>
stream
BT
/F1 24 Tf
100 700 Td
(Kabelwege - Test-PDF) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
0000000313 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
465
%%EOF
"""

    with open(file_path, 'wb') as f:
        f.write(pdf_content)

    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"   ✅ {filename} erstellt (minimal PDF, {file_size_mb:.2f} MB)")
    return True


def main():
    """Hauptfunktion zum Erstellen aller Test-Dateien"""

    print("\n" + "="*60)
    print("📸 Test-Bilder und PDFs generieren")
    print("="*60)

    # Erstelle Bilder-Verzeichnis falls nicht vorhanden
    BILDER_DIR.mkdir(exist_ok=True)
    print(f"\n📁 Zielverzeichnis: {BILDER_DIR}")

    # Prüfe Dependencies
    print("\n🔍 Prüfe Dependencies:")
    print(f"   {'✅' if PIL_AVAILABLE else '❌'} Pillow (für JPG-Bilder)")
    print(f"   {'✅' if REPORTLAB_AVAILABLE else '⚠️ '} ReportLab (für PDFs)")

    if not PIL_AVAILABLE:
        print("\n💡 Tipp: Installiere Pillow für bessere Bilder:")
        print("   pip install Pillow")

    if not REPORTLAB_AVAILABLE:
        print("\n💡 Tipp: Installiere ReportLab für bessere PDFs:")
        print("   pip install reportlab")

    print("\n📤 Erstelle Test-Dateien:")

    success_count = 0

    # Bilder erstellen
    test_images = [
        ("zaehler.jpg", "ZÄHLERSCHRANK", (60, 100, 180)),
        ("hausanschluss.jpg", "HAUSANSCHLUSS", (100, 140, 80)),
        ("montageort.jpg", "MONTAGEORT", (180, 100, 60)),
    ]

    for filename, title, color in test_images:
        if create_test_image(filename, title, color):
            success_count += 1

    # PDF erstellen
    if create_test_pdf("kabelwege.pdf"):
        success_count += 1

    # Zusammenfassung
    print("\n" + "="*60)
    if success_count == 4:
        print("🎉 Alle Test-Dateien erfolgreich erstellt!")
    else:
        print(f"⚠️  {success_count}/4 Dateien erstellt")

    print("\n📋 Erstelle Dateien:")
    for file in BILDER_DIR.iterdir():
        if file.is_file():
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"   {file.name} ({size_mb:.2f} MB)")

    print("\n✅ Bereit für Tests!")
    print("   Führe aus: python test_precheck_automated.py")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
