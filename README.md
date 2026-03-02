# 💼 Job Auto-Apply Tool

> Resume upload karo, preferences set karo — LinkedIn, Indeed, Remotive aur Naukri pe automatically apply karo. Session khatam hone pe email summary milega.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red?logo=streamlit)
![Selenium](https://img.shields.io/badge/Selenium-4.18%2B-green?logo=selenium)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

| Feature | Detail |
|---------|--------|
| 📄 Resume Parsing | PDF + DOCX — name, email, phone, skills, experience auto-extract |
| 🔍 Multi-platform Job Search | LinkedIn Easy Apply, Indeed, Remotive (free API), Naukri |
| 🤖 Auto Apply | Selenium — visible browser mode, tum dekh sakte ho |
| 📸 Screenshot Proof | Har apply ke baad screenshot `screenshots/` mein save |
| 📧 Email Notification | Session khatam hone pe HTML summary email |
| 💰 Auto Currency | India → ₹INR, Other countries → $USD auto-detect |
| 🌍 Location Filter | Country + City choose karo |
| 📊 Tracker + Export | Application history + Excel export |

---

## 📁 Project Structure

```
job-auto-apply/
├── app.py              ← Main Streamlit UI
├── resume_parser.py    ← PDF + DOCX parser
├── job_fetcher.py      ← Job search (all platforms)
├── auto_applicator.py  ← Selenium automation
├── notifier.py         ← Gmail email summary
├── tracker.py          ← Application logger + Excel
├── config.env          ← ⚠️ Credentials (DO NOT COMMIT)
├── requirements.txt    ← Dependencies
└── README.md
```

---

## 🚀 Installation

### 1. Clone karo

```bash
git clone https://github.com/YOUR_USERNAME/job-auto-apply.git
cd job-auto-apply
```

### 2. Virtual environment banao (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Dependencies install karo

```bash
pip install -r requirements.txt
```

### 4. Google Chrome install karo

Download: https://www.google.com/chrome/

> ChromeDriver automatically install ho jaata hai `webdriver-manager` se.

---

## ⚙️ Configuration

`config.env` file kholo aur fill karo:

```env
# Notification — jis email pe summary chahiye
NOTIFY_EMAIL=your_email@gmail.com

# Gmail SMTP — email bhejne ke liye
# App Password: https://myaccount.google.com/apppasswords
SMTP_USER=your_gmail@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx

# Platform credentials
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword
NAUKRI_EMAIL=your@email.com
NAUKRI_PASSWORD=yourpassword
```

### Gmail App Password kaise banaye?

1. Gmail account mein jao → **Google Account** → **Security**
2. **2-Step Verification** ON karo (agar nahi hai)
3. Wapas Security page pe jao → **App passwords**
4. "Select app" → **Mail**, "Select device" → **Windows Computer**
5. **Generate** karo — 16-character password milega
6. Ye password `SMTP_PASS` mein daalo (spaces ke saath ya bina)

---

## ▶️ Run karo

```bash
# Windows
python -m streamlit run app.py

# Mac/Linux
streamlit run app.py
```

Browser automatically khulega: **http://localhost:8501**

---

## 🖥️ Kaise Use Karein (Step by Step)

```
Step 1 → Sidebar: Resume upload karo (PDF ya DOCX)
         ↓ Skills, experience, email auto-extract hoga

Step 2 → Sidebar: Job preferences set karo
         - Job Title: "Python Developer"
         - Work Type: Remote / On-site / Hybrid
         - Experience: Entry / Mid / Senior
         - Country + City
         - Salary range (auto ₹ ya $ based on country)

Step 3 → Sidebar: Platforms check karo
         ✅ LinkedIn Easy Apply
         ✅ Indeed
         ✅ Remotive
         ✅ Naukri

Step 4 → "Find Jobs" tab → "Jobs Dhundo" click karo
         Match score dikhega resume vs job description

Step 5 → "Auto Apply" tab → "Start Auto Apply!" click karo
         - Browser window khulega
         - Tum dekh sakte ho kya ho raha hai
         - Screenshots automatically save honge

Step 6 → Session khatam → Email summary aayega
         - Kitne jobs apply hue
         - Kitne failed
         - Full table with details

Step 7 → "Tracker" tab → history dekho + Excel export karo
```

---

## 📸 Screenshot Proof

Har application ke 3 screenshots automatically save hoti hain:

| Screenshot | Matlab |
|-----------|--------|
| `before_apply_Company_TIME.png` | Job page khuli |
| `before_submit_Company_TIME.png` | Submit se pehle |
| `linkedin_PROOF_Company_TIME.png` | ✅ Apply confirm hua |

Saari screenshots `screenshots/` folder mein milegi.

---

## 📧 Email Notification

Session khatam hone pe HTML email milega jisme:

- ✅ Applied / ❌ Failed / ⚠️ Pending count
- Success rate percentage
- Har application ki details (company, role, platform, time)
- Color-coded table

Tracker tab se manually bhi bhej sakte ho anytime.

---

## ⚠️ Platform Behaviour

| Platform | Auto Apply? | Notes |
|----------|-------------|-------|
| **LinkedIn Easy Apply** | ✅ Yes | Sirf "Easy Apply" wali jobs, login required |
| **Indeed** | ✅ Partial | Simple forms automate, complex forms manual |
| **Remotive** | 🔗 Opens browser | Company site pe redirect, no login needed |
| **Naukri** | ✅ Yes | Quick Apply button click karta hai |

### Captcha ke baare mein

Kuch sites captcha use karti hain — **browser visible hai** isliye tum manually solve kar sakte ho aur tool aage badh jaayega.

---

## 🔧 Troubleshooting

**`ModuleNotFoundError: No module named 'resume_parser'`**
```bash
# Make sure tum project folder mein ho
cd job-auto-apply
python -m streamlit run app.py
```

**ChromeDriver error?**
```bash
pip install --upgrade webdriver-manager
```

**`selenium` not found?**
```bash
pip install selenium webdriver-manager
```

**Email nahi aaya?**
- Gmail → IMAP enabled hai?
- App Password sahi hai? (normal password kaam nahi karta)
- `SMTP_USER` aur `SMTP_PASS` config.env mein hain?

**LinkedIn block kar raha hai?**
- Delay badha do (15-20 seconds)
- `config.env` mein sahi credentials hain?
- LinkedIn 2FA ON hai toh temporarily OFF karo ya manually complete karo

---

## 🔐 Security

- `config.env` kabhi GitHub pe push mat karo
- `.gitignore` already `config.env` ko exclude karta hai
- Credentials sirf local machine pe rehte hain

---

## 📜 .gitignore

```
config.env
*.json
screenshots/
venv/
__pycache__/
*.pyc
.env
```

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Browser Automation**: Selenium + WebDriver Manager
- **PDF Parsing**: pdfplumber + PyMuPDF
- **DOCX Parsing**: python-docx
- **Email**: smtplib (Gmail SMTP)
- **Data**: pandas + openpyxl

---

## ⚖️ Disclaimer

Automated job applications kuch platforms ke Terms of Service ke against ho sakti hain (especially LinkedIn). Is tool ko apne risk pe use karo. Developers kisi bhi account ban ya other consequences ke liye responsible nahi hain.

---

## 🤝 Contributing

PRs welcome hain! Issues mein batao agar koi platform ka apply flow change ho gaya ho.

---

**Good luck with your job search! 🎯**
