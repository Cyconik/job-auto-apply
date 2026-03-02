import streamlit as st
import time
import os
from pathlib import Path
from datetime import datetime

# Load credentials from config.env
try:
    from dotenv import load_dotenv
    load_dotenv("config.env")
except ImportError:
    pass


st.set_page_config(
    page_title="Job Auto-Apply Tool",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem; border-radius: 12px; color: white;
        text-align: center; margin-bottom: 2rem;
    }
    .stat-card {
        background: white; padding: 1.2rem; border-radius: 10px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center;
    }
    .job-card {
        background: #f8f9ff; padding: 1rem; border-radius: 8px;
        border: 1px solid #e0e4ff; margin-bottom: 0.8rem;
    }
    .badge {
        display: inline-block; padding: 2px 10px; border-radius: 20px;
        font-size: 0.75rem; font-weight: 600;
    }
    .badge-linkedin { background: #e8f0fe; color: #1a73e8; }
    .badge-indeed   { background: #fff3e0; color: #e65100; }
    .badge-remotive { background: #e8f5e9; color: #2e7d32; }
    .badge-naukri   { background: #fce4ec; color: #c62828; }
    div[data-testid="stSidebarContent"] { background: #f0f2ff; }
</style>
""", unsafe_allow_html=True)

# ── session state ──────────────────────────────────────────
for k, v in {"resume_data": None, "applications": [], "jobs_found": [], "applying": False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

import resume_parser, job_fetcher, auto_applicator, tracker, notifier

# ── HEADER ────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>💼 Job Auto-Apply Tool</h1>
    <p style="margin:0;opacity:0.9;">Resume upload karo, preferences set karo — baaki sab automatic!</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Preferences")
    st.divider()

    # ── Resume ──────────────────────────────────────────
    st.markdown("### 📄 Resume")
    uploaded_file = st.file_uploader("PDF ya DOCX upload karo", type=["pdf", "docx"])
    if uploaded_file:
        with st.spinner("Parsing..."):
            rd = resume_parser.parse(uploaded_file)
            st.session_state.resume_data = rd
        st.success(f"✅ {len(rd.get('skills', []))} skills found!")

    st.divider()

    # ── Job Preferences ─────────────────────────────────
    st.markdown("### 🎯 Job Preferences")
    job_title  = st.text_input("Job Title / Role", placeholder="e.g. Python Developer")
    work_type  = st.radio("Work Type", ["Remote 🌐", "On-site 🏢", "Hybrid 🔄"], horizontal=True)
    exp_level  = st.select_slider(
        "Experience Level",
        options=["Internship", "Entry", "Mid", "Senior", "Lead"],
        value="Mid",
        label_visibility="visible"
    )

    st.divider()

    # ── Location ────────────────────────────────────────
    st.markdown("### 🌍 Location")
    COUNTRIES = [
        "India 🇮🇳", "Any 🌐", "United States 🇺🇸", "United Kingdom 🇬🇧",
        "Canada 🇨🇦", "Germany 🇩🇪", "Australia 🇦🇺", "Singapore 🇸🇬",
        "UAE 🇦🇪", "Netherlands 🇳🇱"
    ]
    country = st.selectbox("Country", COUNTRIES)
    city    = st.text_input("City (optional)", placeholder="e.g. Bangalore, New York")

    # ── Salary (auto currency) ──────────────────────────
    st.divider()
    st.markdown("### 💰 Expected Salary")
    _is_india = country.startswith("India") or country.startswith("Any")
    if _is_india:
        _sym, _min, _max, _def, _step, _lbl = "₹", 200000, 6000000, (400000, 2000000), 100000, "INR / year"
    else:
        _sym, _min, _max, _def, _step, _lbl = "$", 20000, 400000, (60000, 150000), 5000, "USD / year"

    salary_range = st.slider(
        f"{_lbl}",
        min_value=_min, max_value=_max, value=_def, step=_step,
        format=f"{_sym}%d"
    )

    st.divider()

    # ── Platforms ───────────────────────────────────────
    st.markdown("### 🖥️ Platforms")
    plat_checks = {
        "LinkedIn Easy Apply": st.checkbox("LinkedIn Easy Apply 💼", value=True),
        "Indeed":              st.checkbox("Indeed 🔍",              value=True),
        "Remotive":            st.checkbox("Remotive 🌐",            value=True),
        "Naukri":              st.checkbox("Naukri.com 🇮🇳",         value=True),
    }
    selected_platforms = [p for p, v in plat_checks.items() if v]

    st.divider()

    # ── Apply Settings ──────────────────────────────────
    st.markdown("### ⚙️ Apply Settings")
    max_jobs      = st.number_input("Max applications", 1, 100, 20)
    delay_sec     = st.slider("Delay between applies (sec)", 3, 30, 8)

    st.divider()

    # ── Notification Email ──────────────────────────────
    st.markdown("### 🔔 Notification Email")
    st.caption("Session khatam hone pe summary email aayega")
    notif_email = st.text_input(
        "Your email",
        placeholder="you@gmail.com",
        value=os.environ.get("NOTIFY_EMAIL", "")
    )
    st.caption("Gmail SMTP settings `config.env` mein set karo")

# ══════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Dashboard", "🔍 Find Jobs", "🚀 Auto Apply", "📊 Tracker"])

# ── TAB 1: Dashboard ──────────────────────────────────────
with tab1:
    rd = st.session_state.resume_data
    if rd:
        c1, c2, c3, c4 = st.columns(4)
        for col, icon, label, val in [
            (c1, "📋", "Skills",      len(rd.get("skills", []))),
            (c2, "💼", "Experience",  rd.get("experience_years", "N/A")),
            (c3, "🎓", "Education",   rd.get("education_level", "N/A")),
            (c4, "✅", "Applied",     len(st.session_state.applications)),
        ]:
            col.markdown(f"""
            <div class="stat-card">
                <div style="font-size:2rem">{icon}</div>
                <div style="font-size:1.6rem;font-weight:700;color:#667eea">{val}</div>
                <div style="font-size:0.85rem;color:#666">{label}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("#### 🛠️ Extracted Skills")
            skills = rd.get("skills", [])
            if skills:
                st.markdown(" ".join(f"`{s}`" for s in skills[:25]))
            else:
                st.info("Koi skill nahi mili resume mein")
        with col_r:
            st.markdown("#### 👤 Profile")
            st.markdown(f"**Name:** {rd.get('name','N/A')}")
            st.markdown(f"**Email:** {rd.get('email','N/A')}")
            st.markdown(f"**Phone:** {rd.get('phone','N/A')}")
            summary = rd.get('summary','N/A')
            st.markdown(f"**Summary:** {summary[:200]}{'...' if len(summary)>200 else ''}")
    else:
        st.info("👈 Sidebar mein resume upload karo shuru karne ke liye!")
        st.markdown("""
        ### Kaise use karein:
        1. **Resume upload karo** (PDF ya DOCX)
        2. **Job title & preferences** set karo sidebar mein
        3. **Find Jobs** tab → jobs search karo
        4. **Auto Apply** tab → ek click mein apply karo
        5. **Tracker** tab → results dekho + email summary pao
        """)

# ── TAB 2: Find Jobs ──────────────────────────────────────
with tab2:
    st.markdown("### 🔍 Job Search")

    if not st.session_state.resume_data:
        st.warning("⚠️ Pehle resume upload karo!")
    elif not job_title:
        st.warning("⚠️ Sidebar mein Job Title enter karo!")
    else:
        col_btn, col_info = st.columns([1, 3])
        with col_btn:
            search_btn = st.button("🔍 Jobs Dhundo", type="primary", use_container_width=True)
        with col_info:
            st.caption(f"Searching: **{', '.join(selected_platforms) or 'none selected'}**")

        if search_btn:
            if not selected_platforms:
                st.error("Koi platform select nahi hai!")
            else:
                prefs = {
                    "job_title":     job_title,
                    "work_type":     work_type.split()[0].lower(),
                    "country":       country.split()[0],
                    "city":          city,
                    "salary_min":    salary_range[0],
                    "salary_max":    salary_range[1],
                    "exp_level":     exp_level,
                    "platforms":     selected_platforms,
                    "max_jobs":      int(max_jobs),
                }
                with st.spinner("Jobs fetch ho rahi hain..."):
                    jobs = job_fetcher.fetch_all(prefs, st.session_state.resume_data)
                    st.session_state.jobs_found = jobs
                st.success(f"✅ {len(jobs)} jobs mili!")

        if st.session_state.jobs_found:
            st.markdown(f"#### 📋 {len(st.session_state.jobs_found)} Jobs Found")
            filter_p = st.selectbox("Platform filter", ["All"] + selected_platforms)

            for job in st.session_state.jobs_found:
                if filter_p != "All" and job.get("platform") != filter_p:
                    continue
                p = job.get("platform", "")
                badge = {"LinkedIn Easy Apply":"badge-linkedin","Indeed":"badge-indeed",
                         "Remotive":"badge-remotive","Naukri":"badge-naukri"}.get(p,"badge-linkedin")
                st.markdown(f"""
                <div class="job-card">
                    <span class="badge {badge}">{p}</span>
                    <strong> {job.get('title','N/A')}</strong><br>
                    🏢 {job.get('company','N/A')} &nbsp;|&nbsp;
                    📍 {job.get('location','N/A')} &nbsp;|&nbsp;
                    💰 {job.get('salary','Not disclosed')} &nbsp;|&nbsp;
                    🎯 Match: <strong>{job.get('match_score',0)}%</strong>
                </div>""", unsafe_allow_html=True)

# ── TAB 3: Auto Apply ─────────────────────────────────────
with tab3:
    st.markdown("### 🚀 Auto Apply")

    if not st.session_state.resume_data:
        st.warning("⚠️ Resume upload karo pehle!")
    elif not st.session_state.jobs_found:
        st.warning("⚠️ Pehle 'Find Jobs' tab se jobs dhundo!")
    else:
        total_found   = len(st.session_state.jobs_found)
        total_applied = len(st.session_state.applications)

        c1, c2, c3 = st.columns(3)
        c1.metric("Jobs Found",  total_found)
        c2.metric("Applied",     total_applied)
        c3.metric("Remaining",   total_found - total_applied)

        st.divider()
        st.info(
            "ℹ️ Browser window khulega — tum dekh sakte ho kya ho raha hai. "
            "Apply hone pe screenshot automatically save hogi `screenshots/` folder mein. "
            "Session khatam hone pe email summary milega."
        )

        col_a, col_s = st.columns(2)
        apply_btn = col_a.button("🚀 Start Auto Apply!", type="primary",
                                 use_container_width=True,
                                 disabled=st.session_state.applying)
        stop_btn  = col_s.button("⏹️ Stop",
                                  use_container_width=True,
                                  disabled=not st.session_state.applying)

        if stop_btn:
            st.session_state.applying = False
            st.warning("Stopped!")

        if apply_btn:
            st.session_state.applying = True
            progress_bar = st.progress(0)
            status_box   = st.empty()
            log_area     = st.container()

            already_urls = {a.get("url") for a in st.session_state.applications}
            queue = [j for j in st.session_state.jobs_found if j.get("url") not in already_urls]
            queue = queue[:int(max_jobs)]

            if not queue:
                st.warning("Sab jobs pe already apply ho chuka hai!")
                st.session_state.applying = False
            else:
                for i, job in enumerate(queue):
                    if not st.session_state.applying:
                        break

                    progress_bar.progress((i + 1) / len(queue))
                    status_box.markdown(
                        f"⏳ Applying **{i+1}/{len(queue)}**: "
                        f"**{job['title']}** at **{job['company']}** ({job['platform']})"
                    )

                    result = auto_applicator.apply(job, st.session_state.resume_data, uploaded_file)
                    result.update({
                        "job_title": job.get("title",""),
                        "company":   job.get("company",""),
                        "platform":  job.get("platform",""),
                        "location":  job.get("location",""),
                        "salary":    job.get("salary",""),
                        "url":       job.get("url",""),
                    })
                    st.session_state.applications.append(result)
                    tracker.log(result)

                    icon = {"applied":"✅","failed":"❌","pending":"⚠️"}.get(result["status"],"ℹ️")
                    with log_area:
                        st.markdown(
                            f"{icon} **{job['company']}** — {job['title']} "
                            f"→ `{result['status'].upper()}` — {result.get('note','')}"
                        )

                    if i < len(queue) - 1:
                        time.sleep(delay_sec)

                st.session_state.applying = False
                apps_done = st.session_state.applications

                # ── Send notification email ──────────────────
                if notif_email:
                    with st.spinner("Summary email bhej raha hoon..."):
                        ok, msg = notifier.send_summary(notif_email, apps_done)
                    if ok:
                        st.success(f"📧 Summary email bheja: {notif_email}")
                    else:
                        st.warning(f"Email bhejne mein dikkat: {msg}")

                applied_n = sum(1 for a in apps_done if a["status"] == "applied")
                st.success(f"🎉 Done! {applied_n} applications successful out of {len(queue)}!")

# ── TAB 4: Tracker ────────────────────────────────────────
with tab4:
    st.markdown("### 📊 Application Tracker")
    apps = tracker.load_all()

    # ── Manual email send ────────────────────────────────
    with st.expander("📧 Manually Send Summary Email", expanded=False):
        manual_email = st.text_input(
            "Email address",
            value=notif_email if notif_email else "",
            placeholder="you@gmail.com",
            key="manual_email"
        )
        if st.button("📤 Send Summary Now"):
            if not manual_email:
                st.error("Email address enter karo!")
            elif not apps:
                st.warning("Koi application nahi hai abhi tak!")
            else:
                with st.spinner("Sending..."):
                    ok, msg = notifier.send_summary(manual_email, apps)
                if ok:
                    st.success(f"✅ Email sent to {manual_email}!")
                else:
                    st.error(f"Failed: {msg}")

    st.divider()

    if not apps:
        st.info("Abhi tak koi application nahi hui. 'Auto Apply' tab use karo!")
    else:
        applied = sum(1 for a in apps if a.get("status") == "applied")
        failed  = sum(1 for a in apps if a.get("status") == "failed")
        pending = sum(1 for a in apps if a.get("status") == "pending")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total",      len(apps))
        c2.metric("✅ Applied", applied)
        c3.metric("❌ Failed",  failed)
        c4.metric("⏳ Pending", pending)

        st.divider()

        col_exp, col_clear, _ = st.columns([1, 1, 3])
        with col_exp:
            if st.button("📥 Export Excel"):
                path = tracker.export_excel(apps)
                with open(path, "rb") as f:
                    st.download_button(
                        "⬇️ Download",
                        f,
                        file_name="job_applications.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        with col_clear:
            if st.button("🗑️ Clear All"):
                tracker.clear_all()
                st.session_state.applications = []
                st.rerun()

        import pandas as pd
        df = pd.DataFrame(apps)
        display_cols = [c for c in ["timestamp","company","job_title","platform","location","salary","status","note"] if c in df.columns]

        def _color(val):
            return {"applied":"background-color:#c8e6c9","failed":"background-color:#ffcdd2",
                    "pending":"background-color:#fff9c4"}.get(val,"")

        st.dataframe(
            df[display_cols].style.map(_color, subset=["status"]),
            use_container_width=True,
            height=400
        )
