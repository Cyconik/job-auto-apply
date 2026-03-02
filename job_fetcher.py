"""
job_fetcher.py — LinkedIn, Indeed, Remotive, Naukri
"""
import requests
import time
import random
from urllib.parse import quote_plus

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_all(prefs: dict, resume_data: dict) -> list:
    all_jobs = []
    fetchers = {
        "LinkedIn Easy Apply": _linkedin,
        "Indeed":              _indeed,
        "Remotive":            _remotive,
        "Naukri":              _naukri,
    }
    for platform in prefs.get("platforms", []):
        fn = fetchers.get(platform)
        if not fn:
            continue
        try:
            jobs = fn(prefs)
            for j in jobs:
                j["platform"]     = platform
                j["match_score"]  = _match(j, resume_data)
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[{platform}] fetch error: {e}")
        time.sleep(random.uniform(1, 2))

    all_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return all_jobs[:prefs.get("max_jobs", 50)]


# ── REMOTIVE (free public API) ─────────────────────────────
def _remotive(prefs):
    title = prefs.get("job_title", "developer")
    try:
        r = requests.get(
            f"https://remotive.com/api/remote-jobs?search={quote_plus(title)}&limit=25",
            headers=HEADERS, timeout=15
        )
        r.raise_for_status()
        return [{
            "title":       j.get("title",""),
            "company":     j.get("company_name",""),
            "location":    j.get("candidate_required_location","Remote"),
            "salary":      j.get("salary","Not disclosed"),
            "url":         j.get("url",""),
            "description": j.get("description","")[:500],
            "tags":        j.get("tags",[]),
        } for j in r.json().get("jobs",[])]
    except Exception:
        return _demo_jobs(prefs, "Remotive")


# ── INDEED via RSS / Adzuna fallback ──────────────────────
def _indeed(prefs):
    title   = prefs.get("job_title","developer")
    city    = prefs.get("city","")
    country = prefs.get("country","India")
    wt      = prefs.get("work_type","")

    query = quote_plus(title + (" remote" if wt == "remote" else ""))
    loc   = quote_plus(f"{city} {country}".strip())

    try:
        import feedparser
        url  = f"https://www.indeed.com/rss?q={query}&l={loc}&sort=date&limit=25"
        feed = feedparser.parse(url)
        jobs = [{
            "title":       e.get("title",""),
            "company":     e.get("author","N/A"),
            "location":    e.get("location", f"{city} {country}".strip()),
            "salary":      "Not disclosed",
            "url":         e.get("link",""),
            "description": e.get("summary","")[:500],
            "tags":        [],
        } for e in feed.entries[:20]]
        return jobs if jobs else _demo_jobs(prefs, "Indeed")
    except Exception:
        return _adzuna(prefs)


def _adzuna(prefs):
    import os
    app_id  = os.environ.get("ADZUNA_APP_ID","")
    app_key = os.environ.get("ADZUNA_APP_KEY","")
    if not app_id or not app_key:
        return _demo_jobs(prefs, "Indeed")

    CC = {"India":"in","United":"us","United Kingdom":"gb","Canada":"ca",
          "Germany":"de","Australia":"au","Singapore":"sg","UAE":"ae","Any":"in"}
    country = prefs.get("country","India")
    cc = next((v for k, v in CC.items() if k in country), "in")
    title = prefs.get("job_title","developer")

    try:
        r = requests.get(
            f"https://api.adzuna.com/v1/api/jobs/{cc}/search/1"
            f"?app_id={app_id}&app_key={app_key}"
            f"&results_per_page=20&what={quote_plus(title)}",
            headers=HEADERS, timeout=15
        )
        r.raise_for_status()
        jobs = []
        for j in r.json().get("results",[]):
            sal = ""
            if j.get("salary_min"):
                sal = f"${int(j['salary_min']):,} – ${int(j.get('salary_max',j['salary_min'])):,}"
            jobs.append({
                "title":       j.get("title",""),
                "company":     j.get("company",{}).get("display_name","N/A"),
                "location":    j.get("location",{}).get("display_name","N/A"),
                "salary":      sal or "Not disclosed",
                "url":         j.get("redirect_url",""),
                "description": j.get("description","")[:500],
                "tags":        [],
            })
        return jobs if jobs else _demo_jobs(prefs, "Indeed")
    except Exception:
        return _demo_jobs(prefs, "Indeed")


# ── LINKEDIN (public guest API) ───────────────────────────
def _linkedin(prefs):
    title = prefs.get("job_title","developer")
    city  = prefs.get("city","")
    ctry  = prefs.get("country","India")
    wt    = prefs.get("work_type","")

    loc  = f"{city} {ctry}".strip()
    wmap = {"remote":"2","on-site":"1","hybrid":"3"}
    fwt  = wmap.get(wt,"")

    params = f"keywords={quote_plus(title)}&location={quote_plus(loc)}&f_LF=f_AL&sortBy=DD"
    if fwt:
        params += f"&f_WT={fwt}"

    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?{params}&start=0"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 429:
            return _demo_jobs(prefs, "LinkedIn Easy Apply")

        from bs4 import BeautifulSoup
        import re
        soup = BeautifulSoup(r.text, "html.parser")
        jobs = []
        for card in soup.find_all("li")[:20]:
            t  = card.find("h3")
            co = card.find("h4")
            lc = card.find("span", class_=lambda c: c and "location" in c.lower())
            a  = card.find("a", href=True)
            if not t:
                continue
            job_id = ""
            if a:
                m = re.search(r'/jobs/view/(\d+)', a["href"])
                if m:
                    job_id = m.group(1)
            jobs.append({
                "title":       t.get_text(strip=True),
                "company":     co.get_text(strip=True) if co else "N/A",
                "location":    lc.get_text(strip=True) if lc else loc,
                "salary":      "Not disclosed",
                "url":         f"https://www.linkedin.com/jobs/view/{job_id}" if job_id else "",
                "description": "",
                "tags":        [],
            })
        return jobs if jobs else _demo_jobs(prefs, "LinkedIn Easy Apply")
    except Exception:
        return _demo_jobs(prefs, "LinkedIn Easy Apply")


# ── NAUKRI ────────────────────────────────────────────────
def _naukri(prefs):
    title = prefs.get("job_title","developer")
    city  = prefs.get("city","india")

    slug_t = title.lower().replace(" ","-")
    slug_c = city.lower().replace(" ","-") if city else "india"
    url    = f"https://www.naukri.com/{slug_t}-jobs-in-{slug_c}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        jobs = []
        for card in soup.find_all("article", class_=lambda c: c and "jobTuple" in (c or ""))[:20]:
            t   = card.find("a", class_="title")
            co  = card.find("a", class_="subTitle")
            loc = card.find("li", class_="location")
            sal = card.find("li", class_="salary")
            if not t:
                continue
            jobs.append({
                "title":       t.get_text(strip=True),
                "company":     co.get_text(strip=True) if co else "N/A",
                "location":    loc.get_text(strip=True) if loc else city,
                "salary":      sal.get_text(strip=True) if sal else "Not disclosed",
                "url":         t.get("href",""),
                "description": "",
                "tags":        [],
            })
        return jobs if jobs else _demo_jobs(prefs, "Naukri")
    except Exception:
        return _demo_jobs(prefs, "Naukri")


# ── MATCH SCORE ───────────────────────────────────────────
def _match(job, resume_data):
    skills  = [s.lower() for s in resume_data.get("skills",[])]
    job_txt = (job.get("description","") + " " + " ".join(job.get("tags",[]))).lower()
    if not skills or not job_txt:
        return random.randint(55, 85)
    matched = sum(1 for s in skills if s in job_txt)
    return max(50, min(100, int(matched / max(len(skills),1) * 200)))


# ── DEMO FALLBACK ─────────────────────────────────────────
def _demo_jobs(prefs, platform):
    title   = prefs.get("job_title","Developer")
    country = prefs.get("country","India")
    city    = prefs.get("city","Bangalore")

    companies = [
        ("TCS","tcs.com"),("Infosys","infosys.com"),("Wipro","wipro.com"),
        ("HCL Tech","hcltech.com"),("Cognizant","cognizant.com"),
        ("Accenture","accenture.com"),("Amazon","amazon.jobs"),("Google","careers.google.com"),
    ]
    india = "India" in country or "Any" in country
    jobs  = []
    for i,(co,domain) in enumerate(companies[:8]):
        lvl = ["I","II","Senior","Lead"][min(i//2, 3)]
        sal = (f"₹{8+i*2}L–₹{15+i*3}L" if india else f"${60+i*10}K–${90+i*10}K")
        jobs.append({
            "title":       f"{title} {lvl}",
            "company":     co,
            "location":    f"{city}, {country}",
            "salary":      sal,
            "url":         f"https://{domain}/jobs/demo-{i+1}",
            "description": f"{title} role at {co}. Strong Python and problem-solving required.",
            "tags":        ["Python","SQL","REST API","Git"],
            "_is_demo":    True,
        })
    return jobs
