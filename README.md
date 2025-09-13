# 🔗 URL Shortener
# URL Shortener 🔗

![Python Version](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Build](https://img.shields.io/badge/build-passing-brightgreen)
![GitHub Issues](https://img.shields.io/github/issues/Mehar-2012/url-shortener)
![GitHub Stars](https://img.shields.io/github/stars/Mehar-2012/url-shortener?style=social)

A simple and fast URL shortener built with **Flask** that shortens URLs and tracks analytics.

Transform long URLs into short, shareable links with support for expiration, custom aliases, and detailed analytics.

---

## 🚀 Features

- ✅ Shorten long URLs into unique short codes
- ✅ Redirect from short URL → original URL
- ✅ URL expiration feature (e.g., expires in 7 days)
- ✅ Detects malicious links and prevents spam (too many URLs from same IP).
- ✅ Click analytics: total clicks, last accessed date, and recent activity
- ✅ Simple REST API with JSON responses
- ✅ Lightweight and easy to set up

---

## ⚡ API Usage Examples

### 1️⃣ Create Short URL (POST `/shorten`)

**Request body (JSON):**
```json
{
    "long_url": "https://example.com",
    "expire_days": "7",
    "custom_alias": "myCustomCode"
}

{
    "short_url": "http://127.0.0.1:5000/myCustomCode",
    "short_code": "myCustomCode"
}

2️⃣ Redirect to Original URL (GET /{short_code})

Redirects to the original URL if valid

Returns 410 Gone if expired

Returns 404 Not Found if short code does not exist

3️⃣ URL Analytics (GET /stats/{short_code})

Displays:

Original URL

Created date

Expiration date

Status (Active or Expired)

Total clicks

Last accessed date

Recent activity graph

Architecture Overview

+---------------------+          +------------------+
|     User Browser    |  <--->   |    Flask App     |
| (Form / Short URLs) |          |   (Endpoints)    |
+---------------------+          +------------------+
                                      |
                                      |
                           +------------------------+
                           |      SQLite Database    |
                           | (URLs & Clicks Tables) |
                           +------------------------+

⚙️ Setup & Run Locally

Clone the repository:

git clone https://github.com/Mehar-2012/url-shortener.git
cd url-shortener


Install dependencies:

pip install -r requirements.txt


Run the app:

python app.py


Access the web app at:

http://127.0.0.1:5000/

🛡️ License

This project is licensed under the MIT License.


---

This version is clear, professional, and covers all the features you’ve implemented so far.

Let me know if you want me to export it into a ready-to-use file (`README.md`).




