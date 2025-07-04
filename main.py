from flask import Flask, Response, render_template_string, send_file
import requests
from bs4 import BeautifulSoup
import pdfkit
import os
from queue import Queue
import time

# Flask app
app = Flask(__name__)

# Base URL for fetching coordinates
BASE_URL = "https://mining.cloudflare.manfredi.io/pops/"

# Full list of three-letter PoP codes
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

# Queue to store logs
log_queue = Queue()

# PDF generation function
def generate_pdf():
    html_content = "<h1>Cloudflare PoP Coordinates</h1><ul>"
    for code in POP_CODES:
        # Send log to queue for real-time display
        log_queue.put(f"Grabbing coordinates for {code}...")
        url = BASE_URL + code.lower() + "/"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            coordinates = soup.select_one(COORD_SELECTOR).text.strip()
            html_content += f"<li><b>{code}</b>: {coordinates}</li>"
        except Exception as e:
            html_content += f"<li><b>{code}</b>: Error fetching data</li>"
            log_queue.put(f"Failed to fetch coordinates for {code}.")
        # Simulate delay for a better real-time effect
        time.sleep(0.5)

    # Final log to indicate completion
    log_queue.put("All coordinates have been fetched. PDF is ready for download!")
    html_content += "</ul>"

    # Generate the PDF
    pdf_file = "Cloudflare_PoP_Coordinates.pdf"
    pdfkit.from_string(html_content, pdf_file, configuration=pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf'))
    return pdf_file

# Route for real-time logs via Server-Sent Events (SSE)
@app.route('/logs')
def stream_logs():
    def generate():
        while True:
            log = log_queue.get()  # Wait for new log messages
            yield f"data: {log}\n\n"
    return Response(generate(), mimetype='text/event-stream')

# Route to trigger PDF generation
@app.route('/generate', methods=['GET'])
def generate():
    generate_pdf()
    return "done"

# Homepage route
@app.route('/')
def home():
    # HTML template with real-time logs and "Download PDF" button
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cloudflare PoP Coordinates</title>
        <script>
            // Listen to the server-sent events stream
            const eventSource = new EventSource("/logs");
            eventSource.onmessage = function(event) {
                const logBox = document.getElementById("log-box");
                logBox.innerHTML += event.data + "<br>";
                logBox.scrollTop = logBox.scrollHeight;  // Auto-scroll to the bottom
                if (event.data.includes("PDF is ready for download!")) {
                    document.getElementById("download-btn").style.display = "block";
                }
            };
        </script>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }
            #log-box { border: 1px solid #ddd; padding: 10px; height: 300px; overflow-y: scroll; background: #f9f9f9; }
            #download-btn { display: none; margin-top: 20px; }
            button { padding: 10px 20px; font-size: 16px; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>Cloudflare PoP Coordinates</h1>
        <p>Fetching coordinates... Logs will appear below:</p>
        <div id="log-box"></div>
        <a href="/download" id="download-btn">
            <button>Download PDF</button>
        </a>
        <script>
            // Trigger the backend to start the process
            fetch('/generate');
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

# Route to allow downloading the generated PDF
@app.route('/download', methods=['GET'])
def download_pdf():
    pdf_file = "Cloudflare_PoP_Coordinates.pdf"
    return send_file(pdf_file, as_attachment=True)

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)