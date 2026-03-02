"""
notifier.py
Gmail SMTP se job application summary email bhejta hai.
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def send_summary(to_email: str, applications: list) -> tuple[bool, str]:
    """
    Job application summary email bhejo.
    Returns (success: bool, message: str)
    """
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        return False, "SMTP_USER aur SMTP_PASS config.env mein set nahi hain"

    try:
        subject, html_body = _build_email(applications)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"Job Auto-Apply Tool <{smtp_user}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())

        return True, "Email sent!"

    except smtplib.SMTPAuthenticationError:
        return False, "Gmail login failed — App Password sahi hai? (myaccount.google.com/apppasswords)"
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        return False, str(e)


def _build_email(applications: list) -> tuple[str, str]:
    """HTML email body banao with summary table"""
    total   = len(applications)
    applied = sum(1 for a in applications if a.get("status") == "applied")
    failed  = sum(1 for a in applications if a.get("status") == "failed")
    pending = sum(1 for a in applications if a.get("status") == "pending")
    rate    = int(applied / total * 100) if total else 0

    subject = f"💼 Job Apply Summary — {applied}/{total} applications ({datetime.now().strftime('%d %b %Y')})"

    # Build rows
    rows_html = ""
    for a in applications:
        status = a.get("status", "")
        color  = {"applied": "#c8e6c9", "failed": "#ffcdd2", "pending": "#fff9c4"}.get(status, "#fff")
        icon   = {"applied": "✅", "failed": "❌", "pending": "⚠️"}.get(status, "")
        rows_html += f"""
        <tr style="background:{color}">
            <td style="padding:8px;border:1px solid #ddd">{a.get('timestamp','')}</td>
            <td style="padding:8px;border:1px solid #ddd"><strong>{a.get('company','')}</strong></td>
            <td style="padding:8px;border:1px solid #ddd">{a.get('job_title','')}</td>
            <td style="padding:8px;border:1px solid #ddd">{a.get('platform','')}</td>
            <td style="padding:8px;border:1px solid #ddd">{a.get('location','')}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:center">{icon} {status.upper()}</td>
            <td style="padding:8px;border:1px solid #ddd;font-size:0.85em;color:#555">{a.get('note','')[:80]}</td>
        </tr>"""

    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;max-width:900px;margin:auto;padding:20px;color:#333">

  <div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:24px;border-radius:12px;color:white;text-align:center;margin-bottom:24px">
    <h1 style="margin:0;font-size:1.8rem">💼 Job Application Summary</h1>
    <p style="margin:8px 0 0;opacity:0.9">{datetime.now().strftime('%A, %d %B %Y — %I:%M %p')}</p>
  </div>

  <!-- Stats -->
  <table style="width:100%;border-collapse:collapse;margin-bottom:24px">
    <tr>
      <td style="text-align:center;padding:16px;background:#e8f5e9;border-radius:8px">
        <div style="font-size:2rem;font-weight:bold;color:#2e7d32">{applied}</div>
        <div style="color:#555">✅ Applied</div>
      </td>
      <td style="width:12px"></td>
      <td style="text-align:center;padding:16px;background:#ffebee;border-radius:8px">
        <div style="font-size:2rem;font-weight:bold;color:#c62828">{failed}</div>
        <div style="color:#555">❌ Failed</div>
      </td>
      <td style="width:12px"></td>
      <td style="text-align:center;padding:16px;background:#fff8e1;border-radius:8px">
        <div style="font-size:2rem;font-weight:bold;color:#f57c00">{pending}</div>
        <div style="color:#555">⚠️ Pending</div>
      </td>
      <td style="width:12px"></td>
      <td style="text-align:center;padding:16px;background:#e8eaf6;border-radius:8px">
        <div style="font-size:2rem;font-weight:bold;color:#3949ab">{rate}%</div>
        <div style="color:#555">Success Rate</div>
      </td>
    </tr>
  </table>

  <!-- Table -->
  <h2 style="color:#667eea;border-bottom:2px solid #667eea;padding-bottom:8px">📋 All Applications</h2>
  <table style="width:100%;border-collapse:collapse;font-size:0.9rem">
    <thead>
      <tr style="background:#667eea;color:white">
        <th style="padding:10px;border:1px solid #ddd;text-align:left">Time</th>
        <th style="padding:10px;border:1px solid #ddd;text-align:left">Company</th>
        <th style="padding:10px;border:1px solid #ddd;text-align:left">Role</th>
        <th style="padding:10px;border:1px solid #ddd;text-align:left">Platform</th>
        <th style="padding:10px;border:1px solid #ddd;text-align:left">Location</th>
        <th style="padding:10px;border:1px solid #ddd;text-align:left">Status</th>
        <th style="padding:10px;border:1px solid #ddd;text-align:left">Note</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>

  <p style="color:#999;font-size:0.8rem;margin-top:24px;text-align:center">
    Job Auto-Apply Tool — Good luck with your applications! 🎯
  </p>
</body>
</html>"""

    return subject, html
