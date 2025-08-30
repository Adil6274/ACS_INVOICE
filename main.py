from flask import Flask, render_template, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Path, Circle, Rect, Polygon
from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import qrcode
import os
import datetime
import io
import re  # Needed for terms procprocessing

app = Flask(__name__)

# Page dimensions (needed for watermark layout)
page_width, page_height = A4


def generate_invoice_number():
    filename = 'last_invoice.txt'
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                last_num = int(f.read().strip())
        else:
            last_num = 0
        new_num = last_num + 1
        with open(filename, 'w') as f:
            f.write(str(new_num))
        return f'INV-{new_num:04d}'
    except Exception as e:
        raise RuntimeError(f"Error generating invoice number: {e}")


def generate_qr_code(data, filename):
    qr = qrcode.QRCode(box_size=3, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)


def draw_professional_watermark(c):
    """
    Draws a modern, realistic watermark using two layered images:
    1. Abstract flow background
    2. Food sketch illustration
    """
    abstract_path = "images (13)_NuOsLPh57c.png"  # from image 1
    sketch_path = "images (14)_usQD1mXe0k.png"  # from image 2
    try:
        # Background abstract curves
        c.saveState()
        c.setFillAlpha(0.12)
        bg = ImageReader(abstract_path)
        c.drawImage(bg, 0, 0, width=page_width, height=page_height, mask='auto')
        c.restoreState()

        # Food sketch elements
        c.saveState()
        c.setFillAlpha(0.12)
        sketch = ImageReader(sketch_path)
        sketch_width = page_width * 0.6
        sketch_height = sketch_width * 1.2

        c.drawImage(
            sketch,
            x=page_width - sketch_width - 30,
            y=30,
            width=sketch_width,
            height=sketch_height,
            mask='auto'
        )
        c.restoreState()

    except Exception as e:
        print("Error drawing watermark:", e)

    # --- Repeating Bold Invoice Number Text Watermark ---
    #try:
        
        #c.saveState()
        #c.setFont("Helvetica-Bold", 60)
        #c.setFillColorRGB(0.4, 0.4, 0.4)
        #c.setFillAlpha(0.10)
        #step_x = 200
        #step_y = 100

        #width_guard = locals().get('width', page_width)
        #height_guard = locals().get('height', page_height)
        #invoice_guard = locals().get('invoice_number', 'INVOICE')

        #for x in range(-100, int(width_guard) + 200, step_x):
            #for y in range(-100, int(height_guard) + 100, step_y):
                #c.saveState()
                #c.translate(x, y)
                #c.rotate(30)
                #c.drawString(0, 0, invoice_guard)
                #c.restoreState()
        #c.restoreState()

    #except Exception as e:
        #print("Error drawing text watermark:", e)


def draw_modern_header(c):
    # top rule
    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.5)
    c.line(40, 780, 555, 780)
    # Layout metrics
    padding_left = 40
    logo_w, logo_h = 60, 60
    logo_x = padding_left
    logo_y = 775  # slightly below page top to avoid clipping

    # Draw logo (from same folder as this file)
    try:
        logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
        if os.path.exists(logo_path):
            img = ImageReader(logo_path)
            c.saveState()
            c.drawImage(img, logo_x, logo_y, width=logo_w, height=logo_h, mask='auto')
            c.restoreState()
        else:
            # Optional placeholder if missing
            c.saveState()
            c.setFillColor(colors.Color(0.9, 0.92, 0.98))
            c.rect(logo_x, logo_y, logo_w, logo_h, stroke=False, fill=True)
            c.setFillColor(colors.Color(0.6, 0.65, 0.75))
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(logo_x + logo_w / 2, logo_y + logo_h / 2 - 5, "LOGO")
            c.restoreState()
    except Exception as e:
        print("Logo draw error:", e)

    # Company text block to the right of logo
    text_left = logo_x + logo_w + 12
    baseline = logo_y + logo_h - 12

    c.setFillColor(colors.Color(0.2, 0.2, 0.2))
    c.setFont("Helvetica-Bold", 24)
    c.drawString(text_left, baseline - 8, "ADIL CONSULTING SERVICES")

    c.setFont("Helvetica", 11)
    c.setFillColor(colors.Color(0.4, 0.4, 0.4))
    c.drawString(text_left, baseline - 18, "Professional Business Solutions")

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.Color(0.25, 0.28, 0.33))
    c.drawString(text_left, baseline - 28, "Address: 123 Skyline Tower, Dubai Marina, UAE")
    c.drawString(text_left, baseline - 38, "Phone: +916005796490 | Email: peeradil6005@gmail.com")


def draw_invoice_title(c, invoice_number, invoice_date, due_date):
    # Centered blocks below the company header
    title_w, title_h = 155, 40
    meta_w, meta_h = 260, 52
    center_x = page_width / 2.0
    title_x = center_x - (title_w / 2.0)
    title_y = 720  # adjust if needed

    meta_x = center_x - (meta_w / 2.0) + 125
    meta_y = title_y - meta_h - 10

    # Title rectangle
    c.setFillColor(colors.Color(0.95, 0.95, 0.95))
    c.setStrokeColor(colors.Color(0.8, 0.8, 0.8))
    c.setLineWidth(1)
    c.rect(title_x, title_y, title_w, title_h, stroke=True, fill=True)

    # "INVOICE" centered
    c.setFillColor(colors.Color(0.1, 0.1, 0.1))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(title_x + title_w / 2.0, title_y + 15, "INVOICE")

    # Metadata rectangle
    c.setFillColor(colors.Color(0.95, 0.95, 0.95))
    c.setStrokeColor(colors.Color(0.8, 0.8, 0.8))
    c.setLineWidth(1)
    c.rect(meta_x, meta_y, meta_w, meta_h, stroke=True, fill=True)

    # Labels and values
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.Color(0.3, 0.3, 0.3))
    c.drawString(meta_x + 12, meta_y + meta_h - 16, "Invoice #:")

    label_width = c.stringWidth("Invoice #:", "Helvetica-Bold", 10)
    c.setFillColor(colors.red)
    c.drawString(meta_x + 12 + label_width + 6, meta_y + meta_h - 16, f"{invoice_number}")
    c.setFillColor(colors.Color(0.3, 0.3, 0.3))
    c.drawString(meta_x + 12, meta_y + meta_h - 32, f"Date: {invoice_date}")
    c.drawString(meta_x + 12, meta_y + meta_h - 48, f"Due Date: {due_date}")


def draw_client_section(c, client):
    # Lower a bit so it sits below centered invoice blocks
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.Color(0.2, 0.2, 0.2))
    c.drawString(40, 670, "BILL TO:")
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)
    c.drawString(40, 655, client['name'])
    c.drawString(40, 640, client['address'])
    c.drawString(40, 625, client['email'])


def draw_professional_table(c, items):
    if not items:
        return 610, 0.0

    col_positions = [40, 340, 390, 455, 555]  # <-- header/column guides matching your labels

    c.setFillColor(colors.Color(0.95, 0.95, 0.95))
    c.rect(40, 590, 515, 25, fill=True, stroke=False)

    c.setStrokeColor(colors.Color(0.7, 0.7, 0.7))
    c.setLineWidth(1)
    c.line(40, 590, 555, 590)
    c.line(40, 615, 555, 615)

    for x in col_positions[1:-1]:
        c.line(x, 590, x, 615)

    c.setFillColor(colors.Color(0.2, 0.2, 0.2))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 600, "DESCRIPTION")
    c.drawCentredString(350, 600, "QTY")
    c.drawCentredString(420, 600, "UNIT PRICE")
    c.drawCentredString(500, 600, "AMOUNT")

    y_position = 590
    total_amount = 0
    row_height = 20

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)

    for i, item in enumerate(items):
        description = item['description']
        qty = item['qty']
        price = item['price']
        amount = qty * price
        total_amount += amount

        y_row_start = y_position - row_height

        if i % 2 == 0:
            c.setFillColor(colors.Color(0.98, 0.98, 0.98))
            c.rect(40, y_row_start, 515, row_height, fill=True, stroke=False)

        c.setFillColor(colors.black)
        c.drawString(50, y_row_start + 5, description)
        c.drawCentredString(350, y_row_start + 5, str(qty))
        c.drawCentredString(420, y_row_start + 5, f"${price:.2f}")
        c.drawCentredString(500, y_row_start + 5, f"${amount:.2f}")

        c.setStrokeColor(colors.Color(0.9, 0.9, 0.9))
        c.line(40, y_row_start, 555, y_row_start)

        y_position -= row_height

    y_total_start = y_position - row_height
    c.setFillColor(colors.Color(0.9, 0.9, 0.9))
    c.rect(380, y_total_start, 175, row_height, fill=True, stroke=False)

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.Color(0.1, 0.1, 0.1))
    c.drawString(350, y_total_start + 5, "TOTAL AMOUNT:")
    c.drawCentredString(500, y_total_start + 5, f"${total_amount:.2f}")

    c.setStrokeColor(colors.Color(0.7, 0.7, 0.7))
    c.line(40, y_total_start, 555, y_total_start)

    return y_total_start - 30, total_amount


def draw_terms_section(c, terms, y_position):
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.Color(0.2, 0.2, 0.2))
    c.drawString(40, y_position, "TERMS & CONDITIONS")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.Color(0.4, 0.4, 0.4))

    # Pre-written fixed 15 bullet points for consulting business
    prewritten_terms = [
        "All services are provided only after full advance payment.",
        "Payments once made are non-refundable.",
        "Consulting services are delivered digitally/online only.",
        "This invoice serves as proof of payment for consulting services.",
        "No physical goods are sold under this agreement.",
        "Service timelines will be communicated through official email.",
        "Any change in scope may require a new agreement and revised charges.",
        "All intellectual property created remains with Adil Consulting Services until delivery.",
        "Clients must provide accurate and complete information before service begins.",
        "Confidentiality of all client information will be strictly maintained.",
        "Communication must be done only through approved and official channels.",
        "Invoices must be settled in full before commencement of work.",
        "In case of non-cooperation from client, service timelines may be extended.",
        "Disputes, if any, will be resolved under applicable UAE/Indian law.",
        "For all queries or clarifications, contact peeradil6005@gmail.com."
    ]

    y_pos = y_position - 15
    for line in prewritten_terms:
        if y_pos < 100:
            break
        c.drawString(40, y_pos, f"-  {line}")
        y_pos -= 12


def draw_footer(c):
    c.setStrokeColor(colors.Color(0.8, 0.8, 0.8))
    c.line(40, 50, 555, 50)
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.Color(0.5, 0.5, 0.5))
    c.drawCentredString(297.5, 35,
                        "Thank you for your business! | This is a computer-generated invoice and doesn't need signature")


def draw_signature_block(c):
    # Placement near bottom-left, above footer line at y=50
    sig_x = page_width - 226
    sig_y = 115
    line_width = 186
    img_w = 180
    img_h = 75
    img_y_offset = 0   # image sits above thee line
    label_offset_y = -12

    # Try to draw uploaded signature image (signature.png in project root)
    try:
        sig_path = os.path.join(os.path.dirname(__file__), "signature.png")
        if os.path.exists(sig_path):
            img = ImageReader(sig_path)
            c.drawImage(img, sig_x, sig_y + img_y_offset, width=img_w, height=img_h, mask='auto')
    except Exception as e:
        print(f"Signature image not loaded: {e}")

    # Signature line
    c.setStrokeColor(colors.Color(0.6, 0.6, 0.6))
    c.setLineWidth(1)
    c.line(sig_x, sig_y, sig_x + line_width, sig_y)

    # Name and designation
    c.setFillColor(colors.Color(0.2, 0.2, 0.2))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(sig_x, sig_y + label_offset_y, "PEERZADA ADIL")  # Your name
    c.setFont("Helvetica", 11)
    c.drawString(sig_x, sig_y + label_offset_y - 10, "CEO, ADIL CONSULTING SERVICES")  # Your designation + company

    # Optional small caption
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.Color(0.4, 0.4, 0.4))
    c.drawString(sig_x, sig_y - 30, "Authorized Signatory")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        client = {
            'name': request.form.get('client_name', 'Unknown'),
            'address': request.form.get('client_address', 'Unknown'),
            'email': request.form.get('client_email', 'Unknown')
        }
        terms = request.form.get('terms', 'Payment due within 30 days.')
        due_date_offset = int(request.form.get('due_date_offset', 0))

        items = []
        descriptions = request.form.getlist('description')
        qtys = request.form.getlist('qty')
        prices = request.form.getlist('price')
        for desc, qty, price in zip(descriptions, qtys, prices):
            if desc and qty and price:
                try:
                    items.append({
                        'description': desc,
                        'qty': int(qty),
                        'price': float(price)
                    })
                except ValueError:
                    pass

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        invoice_number = generate_invoice_number()
        invoice_date = datetime.datetime.now().strftime('%B %d, %Y')
        due_date = (datetime.datetime.now() + datetime.timedelta(days=due_date_offset)).strftime('%B %d, %Y')

        draw_professional_watermark(c)
        draw_modern_header(c)
        draw_invoice_title(c, invoice_number, invoice_date, due_date)
        draw_client_section(c, client)
        y_pos, total_amount = draw_professional_table(c, items)
        draw_terms_section(c, terms, y_pos)
        draw_footer(c)
        draw_signature_block(c)

        qr_file = f"qr_{invoice_number}.png"
        qr_data = (
            "Company: ADIL CONSULTING SERVICES\n"
            "Address: 123 Skyline Tower, Dubai Marina, UAE\n"
            "Email: peeradil6005@gmail.com\n"
            "Phone: +916005796490\n\n"
            f"Invoice Number: {invoice_number}\n"
            f"Invoice Date: {invoice_date}\n"
            f"Due Date: {due_date}\n\n"
            f"Client Name: {client['name']}\n"
            f"Client Address: {client['address']}\n"
            f"Client Email: {client['email']}\n\n"
            f"Total Amount: ${total_amount:.2f}"
        )
        generate_qr_code(qr_data, qr_file)

        try:
            c.drawImage(ImageReader(qr_file), 495, 715, width=60, height=60)
        except Exception as e:
            print(f"QR image notloadedd: {e}")

        c.save()

        # Save the generated PDF to disk
        try:
            os.makedirs("invoices", exist_ok=True)
            save_path = os.path.join("invoices", f"invoice_{invoice_number}.pdf")
            with open(save_path, "wb") as f_out:
                f_out.write(buffer.getvalue())
            print(f"Saved invoice to: {save_path}")
        except Exception as e:
            print(f"Failed to save invoice: {e}")

        if os.path.exists(qr_file):
            os.remove(qr_file)

        buffer.seek(0)
        return send_file(buffer, as_attachment=True,
                         download_name=f"invoice_{invoice_number}.pdf",
                         mimetype='application/pdf')

    return render_template('index.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

