from flask import Flask, request, jsonify, redirect, render_template_string
import sys
import os

# Add apps folder to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps'))

from database import init_db, SessionLocal, URL
from utils import generate_short_code

app = Flask(__name__)

# Initialize database
try:
    init_db(app)
    print("Database initialized successfully")
except Exception as e:
    print(f"Database error: {e}")
    sys.exit(1)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LinkShrink - URL Shortener</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
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
        
        .form-container {
            margin-bottom: 30px;
        }
        
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
        
        #longUrl::placeholder {
            color: #aaa;
        }
        
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
        
        .shorten-btn:active {
            transform: scale(0.98);
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
        
        #shortUrl:hover {
            color: #764ba2;
        }
        
        .copy-btn {
            background: #4caf50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            margin-left: 10px;
            transition: all 0.3s ease;
        }
        
        .copy-btn:hover {
            background: #45a049;
            transform: scale(1.05);
        }
        
        .copy-btn.copied {
            background: #2196f3;
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
        <div class="subtitle">Transform your long URLs into short, shareable links</div>
        
        <div class="form-container">
            <form id="urlForm">
                <div class="input-group">
                    <input type="url" id="longUrl" placeholder="Paste your long URL here..." required>
                    <button type="submit" class="shorten-btn">
                        <span id="btnText">Shorten URL</span>
                        <div id="loader" class="loader"></div>
                    </button>
                </div>
            </form>
        </div>
        
        <div id="result" class="result">
            <div class="result-label">✨ Your shortened URL is ready!</div>
            <div class="url-container">
                <a id="shortUrl" href="" target="_blank"></a>
                <button class="copy-btn" onclick="copyToClipboard()">Copy</button>
            </div>
            <small style="color: #888;">Click the link to test it or use the copy button to share</small>
        </div>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">⚡</div>
                <div>Fast & Reliable</div>
            </div>
            <div class="feature">
                <div class="feature-icon">🛡️</div>
                <div>Secure Links</div>
            </div>
            <div class="feature">
                <div class="feature-icon">📊</div>
                <div>Easy to Share</div>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('urlForm').onsubmit = function(e) {
            e.preventDefault();
            
            const btnText = document.getElementById('btnText');
            const loader = document.getElementById('loader');
            const result = document.getElementById('result');
            
            // Show loading state
            btnText.style.display = 'none';
            loader.style.display = 'block';
            
            fetch('/shorten', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({long_url: document.getElementById('longUrl').value})
            })
            .then(response => response.json())
            .then(data => {
                if (data.short_url) {
                    document.getElementById('shortUrl').href = data.short_url;
                    document.getElementById('shortUrl').textContent = data.short_url;
                    result.classList.add('show');
                    result.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Something went wrong. Please try again.');
            })
            .finally(() => {
                // Reset button state
                btnText.style.display = 'inline';
                loader.style.display = 'none';
            });
        };
        
        function copyToClipboard() {
            const shortUrl = document.getElementById('shortUrl').textContent;
            navigator.clipboard.writeText(shortUrl).then(function() {
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
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/shorten", methods=["POST"])
def shorten_url():
    data = request.get_json()
    long_url = data.get("long_url")
    
    if not long_url:
        return jsonify({"error": "long_url is required"}), 400
    
    db = SessionLocal()
    try:
        # Generate unique short code
        short_code = generate_short_code()
        
        # Check if code already exists
        while db.query(URL).filter(URL.short_code == short_code).first():
            short_code = generate_short_code()
        
        # Save to database
        new_url = URL(long_url=long_url, short_code=short_code)
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
    db = SessionLocal()
    try:
        url_record = db.query(URL).filter(URL.short_code == short_code).first()
        if url_record:
            return redirect(url_record.long_url)
        else:
            return "URL not found", 404
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting Flask server on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)