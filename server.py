import http.server
import socketserver
import json
import smtplib
import os
import functools
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

GMAIL_USER = os.getenv("GMAIL_USER", "saifmodan000@gmail.com")
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS", "gshovamcmnzcfrvn")

MAX_PAYLOAD_SIZE = 50 * 1024  # 50 KB security limit

class PortfolioRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/contact':
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Security: Prevent payload flood / memory DoS
            if content_length > MAX_PAYLOAD_SIZE:
                self.send_response(413)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Payload too large"}).encode('utf-8'))
                return

            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                # Security: Sanitize inputs against CRLF / header injection
                sender_name = str(data.get('name', 'Anonymous')).replace('\r', '').replace('\n', '').strip()[:100]
                sender_email = str(data.get('email', '')).replace('\r', '').replace('\n', '').strip()[:150]
                message_text = str(data.get('message', '')).strip()[:10000]

                if not sender_name or not sender_email or not message_text:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Missing required fields"}).encode('utf-8'))
                    return

                # Send email via Gmail SMTP
                msg = MIMEMultipart()
                msg['From'] = GMAIL_USER
                msg['To'] = GMAIL_USER
                msg['Reply-To'] = sender_email
                msg['Subject'] = f"🚀 New Portfolio Inquiry from {sender_name}"

                body = f"""Hello Saif,

You have received a new contact message from your portfolio website!

👤 Name: {sender_name}
📧 Email: {sender_email}
🕒 Received At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💬 Message:
----------------------------------------
{message_text}
----------------------------------------

You can reply directly to this email to respond to {sender_name} ({sender_email}).
"""
                msg.attach(MIMEText(body, 'plain'))

                try:
                    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
                    server.starttls()
                    server.login(GMAIL_USER, GMAIL_APP_PASS)
                    server.send_message(msg)
                    server.quit()
                    email_status = "sent"
                except Exception as mail_err:
                    print(f"[SMTP ERROR] {mail_err}")
                    email_status = f"error: {str(mail_err)}"

                response = {
                    "success": True,
                    "status": email_status,
                    "message": "Thank you! Your message has been sent successfully."
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Invalid request payload"}).encode('utf-8'))
                return

        return super().do_POST()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    handler = functools.partial(PortfolioRequestHandler, directory=DIRECTORY)
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        print(f"Portfolio Server running on http://127.0.0.1:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
