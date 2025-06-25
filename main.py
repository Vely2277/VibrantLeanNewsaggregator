from flask import Flask, send_file, render_template_string
import requests
from bs4 import BeautifulSoup
import pdfkit
import os

# Flask app
app = Flask(__name__)

# Base URL for fetching coordinates
BASE_URL = "https://mining.cloudflare.manfredi.io/pops/"

# List of three-letter PoP codes
POP_CODES = [
    "AAE", "ABJ", "ABQ", "ACC", "ADB", "ADD", "ADL", "AKL", "AKX", "ALA", "ALG", "AMD",
    "AMM", "AMS", "ANC", "AQG", "ARI", "ARN", "ARU", "ASK", "ASU", "ATH", "ATL", "AUS",
    "BAH", "BAQ", "BBI", "BCN", "BEG", "BEL", "BEY", "BGI", "BGR", "BGW", "BHY", "BKK",
    "BLR", "BNA", "BNE", "BNU", "BOD", "BOG", "BOM", "BOS", "BPE", "BRU", "BSB", "BSR",
    "BTS", "BUD", "BUF", "BWN", "CAI", "CAN", "CAW", "CBR", "CCP", "CCU", "CDG", "CEB",
    "CFC", "CGB", "CGD", "CGK", "CGO", "CGP", "CGQ", "CGY", "CHC", "CKG", "CLE", "CLO",
    "CLT", "CMB", "CMH", "CMN", "CNF", "CNN", "CNX", "COK", "COR", "CPH", "CPT", "CRK",
    "CSX", "CTU", "CUR", "CWB", "CZX", "DAC", "DAD", "DAR", "DEL", "DEN", "DFW", "DKR",
    "DLC", "DME", "DMM", "DOH", "DPS", "DTW", "DUB", "DUR", "DUS", "DXB", "EBB", "EBL",
    "EDI", "EVN", "EWR", "EZE", "FCO", "FIH", "FLN", "FOC", "FOR", "FRA", "FSD", "FUK",
    "FUO", "GBE", "GDL", "GEO", "GIG", "GND", "GOT", "GRU", "GUA", "GUM", "GVA", "GYD",
    "GYE", "GYN", "HAK", "HAM", "HAN", "HBA", "HEL", "HET", "HFA", "HFE", "HGH", "HKG",
    "HNL", "HNY", "HRE", "HYD", "HYN", "IAD", "IAH", "ICN", "IND", "ISB", "IST", "ISU",
    "ITJ", "IXC", "JAX", "JDO", "JED", "JHB", "JIB", "JJN", "JNB", "JOG", "JOI", "JSR",
    "JUZ", "JXG", "KBP", "KCH", "KEF", "KGL", "KHH", "KHI", "KHN", "KHV", "KIN", "KIV",
    "KIX", "KJA", "KLD", "KMG", "KNU", "KTM", "KUL", "KWE", "KWI", "LAD", "LAS", "LAX",
    "LCA", "LED", "LHE", "LHR", "LHW", "LIM", "LIS", "LLK", "LOS", "LPB", "LUN", "LUX",
    "LYA", "LYS", "MAA", "MAD", "MAN", "MAO", "MBA", "MCI", "MCT", "MDE", "MDL", "MEL",
    "MEM", "MEX", "MFE", "MFM", "MGM", "MIA", "MLE", "MNL", "MPM", "MRS", "MRU", "MSP",
    "MSQ", "MUC", "MXP", "NAG", "NAY", "NBG", "NBO", "NJF", "NKG", "NNG", "NOU", "NQN",
    "NQZ", "NRT", "NTG", "NVT", "OKA", "OKC", "OMA", "ORD", "ORF", "ORK", "ORN", "OSL",
    "OTP", "OUA", "PAP", "PAT", "PBH", "PBM", "PDX", "PEK", "PER", "PHL", "PHX", "PIG",
    "PIT", "PKX", "PMO", "PMW", "PNH", "POA", "POS", "PPT", "PRG", "PTY", "PVG", "QRO",
    "QWJ", "RAO", "RDU", "REC", "RGN", "RIC", "RIX", "ROB", "RUH", "RUN", "SAN", "SAP",
    "SAT", "SCL", "SDQ", "SEA", "SFO", "SGN", "SHA", "SHE", "SIN", "SJC", "SJK", "SJO",
    "SJP", "SJU", "SJW", "SKG", "SKP", "SLC", "SMF", "SOD", "SOF", "SSA", "STI", "STL",
    "STR", "SUV", "SVX", "SYD", "SZV", "SZX", "TAO", "TAS", "TBS", "TEN", "TGU", "TIA",
    "TKO", "TLH", "TLL", "TLV", "TNA", "TNR", "TPA", "TPE", "TSN", "TUN", "TXL", "TYN",
    "UDI", "UIO", "ULN", "URT", "VCP", "VIE", "VIX", "VNO", "VTE", "WAW", "WDH", "WDS",
    "WHU", "WUH", "WUX", "XAP", "XFN", "XIY", "XMN", "XNH", "XNN", "YHZ", "YIH", "YNJ",
    "YOW", "YTY", "YUL", "YVR", "YWG", "YXE", "YYC", "YYZ", "ZAG", "ZDM", "ZGN", "ZRH"
]

# CSS selector for coordinate extraction
COORD_SELECTOR = "body > div > div > main > section.mx-auto.max-w-4xl.space-y-8 > div > div > div:nth-child(1) > div:nth-child(3) > div > p:nth-child(2)"

# Generate PDF with combined coordinates
def generate_pdf():
    html_content = "<h1>Cloudflare PoP Coordinates</h1><ul>"
    for code in POP_CODES:
        url = BASE_URL + code.lower() + "/"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            coordinates = soup.select_one(COORD_SELECTOR).text.strip()
            html_content += f"<li><b>{code}</b>: {coordinates}</li>"
        except Exception as e:
            html_content += f"<li><b>{code}</b>: Error fetching data</li>"

    html_content += "</ul>"
    pdf_file = "Cloudflare_PoP_Coordinates.pdf"
    pdfkit.from_string(html_content, pdf_file, configuration=pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf'))
    return pdf_file

# Flask route to trigger PDF generation and download
@app.route('/download', methods=['GET'])
def download_pdf():
    pdf_file = generate_pdf()
    return send_file(pdf_file, as_attachment=True)

# Home route
@app.route('/')
def home():
    return '''
        <h1>Cloudflare PoP Coordinates</h1>
        <p>Click the button below to generate and download the PDF file of Cloudflare PoP coordinates.</p>
        <a href="/download">
            <button>Download PDF</button>
        </a>
    '''

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)