from flask import Flask, request, jsonify, redirect, render_template_string
from datetime import datetime, timedelta
import sys
import os
import re
from collections import defaultdict

# Add apps folder to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps'))

from database import init_db, SessionLocal, URL, Click
from utils import generate_short_code
from sqlalchemy import func

app = Flask(__name__)

# Rate limiting storage (in-memory)
ip_requests = defaultdict(list)
RATE_LIMIT_MAX = 5  # 5 URLs per hour per IP
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds

# Initialize database
try:
    init_db()
    print("Database initialized successfully")
except Exception as e:
    print(f"Database error: {e}")
    sys.exit(1)

def is_rate_limited(ip):
    """Check if IP is rate limited"""
    now = datetime.now().timestamp()
    # Clean old requests (older than rate limit window)
    ip_requests[ip] = [req_time for req_time in ip_requests[ip] if now - req_time < RATE_LIMIT_WINDOW]
    
    if len(ip_requests[ip]) >= RATE_LIMIT_MAX:
        return True
    
    # Add current request
    ip_requests[ip].append(now)
    return False

def is_malicious_url(url):
    """Basic security check for malicious URLs"""
    if not url.startswith(('http://', 'https://')):
        return True
    
    # Block common malicious patterns
    malicious_patterns = [
        r'localhost',
        r'127\.0\.0\.1',
        r'0\.0\.0\.0',
        r'192\.168\.',
        r'10\.',
        r'172\.1[6-9]\.',
        r'172\.2[0-9]\.',
        r'172\.3[0-1]\.',
        r'bit\.ly',  # Block other shorteners
        r'tinyurl\.com',
        r't\.co',
        r'malware',
        r'phish',
        r'scam'
    ]
    
    for pattern in malicious_patterns:
        if re.search(pattern, url.lower()):
            return True
    
    return False

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LinkShrink - URL Shortener</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 600px;
            width: 100%;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .logo {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 40px;
            font-size: 1.1rem;
        }
        .form-container { margin-bottom: 30px; }
        .input-group {
            display: flex;
            background: white;
            border-radius: 50px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
            overflow: hidden;
            margin-bottom: 20px;
            border: 2px solid #f0f0f0;
            transition: all 0.3s ease;
        }
        .input-group:focus-within {
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.15);
        }
        #longUrl {
            flex: 1;
            border: none;
            padding: 18px 25px;
            font-size: 16px;
            outline: none;
            background: transparent;
        }
        #longUrl::placeholder { color: #aaa; }
        .shorten-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 18px 35px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            border-radius: 50px;
        }
        .shorten-btn:hover {
            transform: translateX(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .shorten-btn:active { transform: scale(0.98); }
        .expiration-options {
            margin-top: 15px;
            text-align: left;
            background: rgba(255, 255, 255, 0.8);
            padding: 15px;
            border-radius: 10px;
        }
        .expiration-options label {
            font-weight: 600;
            color: #666;
        }
        .result {
            background: linear-gradient(135deg, #f8f9ff, #e8f4ff);
            border: 2px solid #e3f2fd;
            border-radius: 15px;
            padding: 25px;
            margin-top: 25px;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.5s ease;
        }
        .result.show {
            opacity: 1;
            transform: translateY(0);
        }
        .result-label {
            color: #2196f3;
            font-weight: 600;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }
        .url-container {
            display: flex;
            align-items: center;
            background: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            margin-bottom: 15px;
        }
        #shortUrl {
            flex: 1;
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.1rem;
        }
        #shortUrl:hover { color: #764ba2; }
        .copy-btn, .stats-btn {
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            margin-left: 10px;
            transition: all 0.3s ease;
        }
        .copy-btn { background: #4caf50; }
        .copy-btn:hover {
            background: #45a049;
            transform: scale(1.05);
        }
        .copy-btn.copied { background: #2196f3; }
        .stats-btn { background: #ff9800; }
        .stats-btn:hover {
            background: #e68900;
            transform: scale(1.05);
        }
        .features {
            display: flex;
            justify-content: space-around;
            margin-top: 30px;
            padding-top: 30px;
            border-top: 1px solid #eee;
        }
        .feature {
            text-align: center;
            color: #666;
        }
        .feature-icon {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        .loader {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
            display: none;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @media (max-width: 600px) {
            .container {
                padding: 30px 20px;
                margin: 10px;
            }
            .input-group {
                flex-direction: column;
                border-radius: 15px;
            }
            .shorten-btn {
                border-radius: 0 0 15px 15px;
            }
            .features {
                flex-direction: column;
                gap: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🔗 LinkShrink</div>
        <div class="subtitle">Transform your long URLs into short, shareable links with analytics</div>
        
        <div class="form-container">
            <form id="urlForm">
                <div class="input-group">
                    <input type="url" id="longUrl" placeholder="Paste your long URL here..." required>
                    <button type="submit" class="shorten-btn">
                        <span id="btnText">Shorten URL</span>
                        <div id="loader" class="loader"></div>
                    </button>
                </div>
                <div class="expiration-options">
                    <label for="expiration">Expiration:</label>
                    <select id="expiration" style="padding: 8px; border-radius: 5px; border: 1px solid #ddd; margin-left: 10px;">
                        <option value="">Never</option>
                        <option value="0.00069">1 Minute</option>
                        <option value="0.003472">5 Minutes</option>
                        <option value="0.0208">30 Minutes</option>
                        <option value="1">1 Day</option>
                        <option value="7">7 Days</option>
                    </select>
                </div>
            </form>
        </div>
        
        <div id="result" class="result">
            <div class="result-label">✨ Your shortened URL is ready!</div>
            <div class="url-container">
                <a id="shortUrl" href="" target="_blank"></a>
                <button class="copy-btn" onclick="copyToClipboard()">Copy</button>
                <button class="stats-btn" onclick="viewStats()">Stats</button>
            </div>
            <small style="color: #888;">Click the link to test it, copy to share, or view stats to track clicks</small>
        </div>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">⚡</div>
                <div>Fast & Reliable</div>
            </div>
            <div class="feature">
                <div class="feature-icon">📊</div>
                <div>Click Analytics</div>
            </div>
            <div class="feature">
                <div class="feature-icon">🛡️</div>
                <div>Secure Links</div>
            </div>
        </div>
    </div>

    <script>
        let currentShortCode = '';
        
        document.getElementById('urlForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const longUrl = document.getElementById('longUrl').value;
            const expiration = document.getElementById('expiration').value;
            document.getElementById('btnText').style.display = 'none';
            document.getElementById('loader').style.display = 'block';

            try {
                const requestData = { long_url: longUrl };
                if (expiration) {
                    requestData.expire_days = parseFloat(expiration);
                }

                const response = await fetch('/shorten', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });

                const data = await response.json();
                if (response.ok) {
                    document.getElementById('shortUrl').textContent = data.short_url;
                    document.getElementById('shortUrl').href = data.short_url;
                    currentShortCode = data.short_code;
                    document.getElementById('result').classList.add('show');
                    document.getElementById('result').style.display = 'block';
                } else {
                    alert(data.error);
                }
            } catch (err) {
                alert('Something went wrong.');
                console.error(err);
            } finally {
                document.getElementById('btnText').style.display = 'inline';
                document.getElementById('loader').style.display = 'none';
            }
        });

        function copyToClipboard() {
            const shortUrl = document.getElementById('shortUrl').textContent;
            navigator.clipboard.writeText(shortUrl).then(() => {
                const copyBtn = document.querySelector('.copy-btn');
                const originalText = copyBtn.textContent;
                copyBtn.textContent = 'Copied!';
                copyBtn.classList.add('copied');
                
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                    copyBtn.classList.remove('copied');
                }, 2000);
            });
        }

        function viewStats() {
            if (currentShortCode) {
                window.open(`/stats/${currentShortCode}`, '_blank');
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/shorten", methods=["POST"])
def shorten_url():
    # Get client IP
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    
    # Check rate limiting
    if is_rate_limited(client_ip):
        return jsonify({"error": "Rate limit exceeded. Maximum 5 URLs per hour."}), 429
    
    data = request.json
    long_url = data.get("long_url")
    expire_days = data.get("expire_days")

    if not long_url:
        return jsonify({"error": "long_url is required"}), 400
    
    # Security check
    if is_malicious_url(long_url):
        return jsonify({"error": "URL blocked for security reasons"}), 400

    db = SessionLocal()
    try:
        short_code = generate_short_code()
        while db.query(URL).filter(URL.short_code == short_code).first():
            short_code = generate_short_code()

        expires_at = None
        if expire_days:
            try:
                expires_at = datetime.utcnow() + timedelta(days=float(expire_days))
            except ValueError:
                return jsonify({"error": "expire_days must be a number"}), 400

        new_url = URL(long_url=long_url, short_code=short_code, expires_at=expires_at)
        db.add(new_url)
        db.commit()

        return jsonify({
            "short_url": f"http://127.0.0.1:5000/{short_code}",
            "short_code": short_code
        })

    finally:
        db.close()

@app.route("/<short_code>")
def redirect_url(short_code):
    print(f"[DEBUG] Received short_code: {short_code}")
    db = SessionLocal()
    try:
        url_record = db.query(URL).filter(URL.short_code == short_code).first()
        print(f"[DEBUG] DB record found: {url_record}")

        if not url_record:
            return "URL not found", 404

        if url_record.expires_at and datetime.utcnow() > url_record.expires_at:
            return """
            <html>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1>⏰ Link Expired</h1>
                    <p>This shortened URL has expired and is no longer available.</p>
                    <a href="/" style="color: #667eea; text-decoration: none;">← Create a new link</a>
                </body>
            </html>
            """, 410

        # Log click
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'Unknown'))
        click = Click(short_code=short_code, ip_address=user_ip)
        db.add(click)
        db.commit()

        return redirect(url_record.long_url)

    finally:
        db.close()

@app.route("/stats/<short_code>")
def get_stats(short_code):
    db = SessionLocal()
    try:
        url_record = db.query(URL).filter(URL.short_code == short_code).first()
        if not url_record:
            return "URL not found", 404

        total_clicks = db.query(Click).filter(Click.short_code == short_code).count()

        last_click = db.query(Click).filter(Click.short_code == short_code).order_by(Click.clicked_at.desc()).first()
        last_accessed = last_click.clicked_at.isoformat() if last_click else None

        clicks_by_day = db.query(
            func.date(Click.clicked_at).label('date'),
            func.count(Click.id).label('count')
        ).filter(
            Click.short_code == short_code
        ).group_by(
            func.date(Click.clicked_at)
        ).order_by(
            func.date(Click.clicked_at).desc()
        ).limit(7).all()

        stats_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Stats for {short_code}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }}
                .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
                .stat-box {{ background: #667eea; color: white; padding: 20px; margin: 15px 0; border-radius: 8px; text-align: center; }}
                .stat-number {{ font-size: 2em; font-weight: bold; }}
                .stat-label {{ font-size: 1.1em; margin-top: 10px; }}
                .chart {{ margin: 20px 0; }}
                .back-btn {{ background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Analytics for {short_code}</h1>
                <p><strong>Original URL:</strong> {url_record.long_url}</p>
                <p><strong>Created:</strong> {url_record.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Expires:</strong> {'Never' if not url_record.expires_at else url_record.expires_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Status:</strong> {'Expired' if url_record.expires_at and datetime.utcnow() > url_record.expires_at else 'Active'}</p>

                <div class="stat-box">
                    <div class="stat-number">{total_clicks}</div>
                    <div class="stat-label">Total Clicks</div>
                </div>

                <div class="stat-box">
                    <div class="stat-number">{'Never' if not last_accessed else last_accessed.split('T')[0]}</div>
                    <div class="stat-label">Last Accessed</div>
                </div>

                <h3>Recent Activity (Last 7 Days)</h3>
                <div class="chart">
        """

        for day_stat in clicks_by_day:
            stats_html += f"""
                    <div style="display: flex; align-items: center; margin: 10px 0;">
                        <div style="width: 100px;">{day_stat.date}</div>
                        <div style="background: #667eea; height: 20px; width: {max(day_stat.count * 20, 20)}px; margin-right: 10px;"></div>
                        <div>{day_stat.count} clicks</div>
                    </div>
            """

        stats_html += """
                </div>
                <a href="/" class="back-btn">← Back to Home</a>
            </div>
        </body>
        </html>
        """

        return stats_html

    finally:
        db.close()

if __name__ == "__main__":
    print("Starting Flask server on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)