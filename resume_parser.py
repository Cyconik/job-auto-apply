"""
resume_parser.py — PDF aur DOCX support
"""
import re
import io


def parse(uploaded_file) -> dict:
    name = uploaded_file.name.lower()
    data = uploaded_file.read()
    uploaded_file.seek(0)
    text = _read_pdf(data) if name.endswith(".pdf") else _read_docx(data)
    return _extract(text)


def _read_pdf(data: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as f:
            return "\n".join(p.extract_text() or "" for p in f.pages)
    except Exception:
        pass
    try:
        import fitz
        doc = fitz.open(stream=data, filetype="pdf")
        return "\n".join(p.get_text() for p in doc)
    except Exception:
        return ""


def _read_docx(data: bytes) -> str:
    try:
        from docx import Document
        return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
    except Exception:
        return ""


def _extract(text: str) -> dict:
    return {
        "raw_text":        text,
        "name":            _name(text),
        "email":           _email(text),
        "phone":           _phone(text),
        "skills":          _skills(text),
        "experience_years": _exp_years(text),
        "education_level": _education(text),
        "summary":         _summary(text),
    }


def _email(t):
    m = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', t)
    return m.group(0) if m else "N/A"


def _phone(t):
    m = re.search(r'(\+?\d[\d\s\-().]{8,14}\d)', t)
    return m.group(0).strip() if m else "N/A"


def _name(t):
    for line in t.split("\n"):
        line = line.strip()
        if 2 < len(line) < 50 and re.match(r'^[A-Za-z\s.]+$', line) and not re.search(r'@|\d', line):
            return line
    return "N/A"


def _summary(t):
    m = re.search(r'(?:summary|objective|profile|about)[:\n]+(.{50,400})', t, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()[:400]
    for para in t.split("\n\n"):
        if len(para.strip()) > 100:
            return para.strip()[:400]
    return "N/A"


def _exp_years(t):
    m = re.search(r'(\d+)\+?\s*years?\s+(?:of\s+)?experience', t, re.IGNORECASE)
    if m:
        return int(m.group(1))
    years = sorted(set(int(y) for y in re.findall(r'\b(20\d\d|19\d\d)\b', t)))
    return max(0, years[-1] - years[0]) if len(years) >= 2 else "N/A"


def _education(t):
    tl = t.lower()
    for level, kws in {
        "PhD":        ["phd","doctorate"],
        "Master's":   ["master","mtech","m.tech","msc","mba"],
        "Bachelor's": ["bachelor","btech","b.tech","bsc","b.sc","b.e"],
        "Diploma":    ["diploma"],
    }.items():
        if any(k in tl for k in kws):
            return level
    return "N/A"


def _skills(t):
    ALL = [
        "Python","Java","JavaScript","TypeScript","C++","C#","Go","Rust","Kotlin","Swift","PHP","Ruby","R","Bash",
        "React","Angular","Vue","Next.js","Node.js","Express","Django","Flask","FastAPI","Spring","HTML","CSS",
        "Tailwind","Bootstrap","REST","GraphQL","Machine Learning","Deep Learning","NLP","TensorFlow","PyTorch",
        "Keras","scikit-learn","Pandas","NumPy","OpenCV","Data Analysis","Data Science","Tableau","Power BI",
        "AWS","Azure","GCP","Docker","Kubernetes","Terraform","CI/CD","Jenkins","Git","Linux","Ansible",
        "SQL","MySQL","PostgreSQL","MongoDB","Redis","Elasticsearch","Firebase","DynamoDB","Hadoop","Spark","Kafka",
        "Android","iOS","Flutter","React Native","Agile","Scrum","Jira","Figma","Blockchain","Solidity",
    ]
    tl = t.lower()
    return [s for s in ALL if s.lower() in tl]
