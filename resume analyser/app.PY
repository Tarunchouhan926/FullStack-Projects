from flask import Flask, render_template, request
import PyPDF2
import docx2txt
import spacy
import re
import mysql.connector
import os
from dotenv import load_dotenv

# ✅ Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
nlp = spacy.load("en_core_web_sm")

# ✅ Connect to MySQL database using environment variables
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME")
)
cursor = conn.cursor()


# ✅ Define your skills list (same as before)
SKILLS_LIST = set([
    "Python", "Java", "C++", "JavaScript", "TypeScript", "C#", "Swift", "Go", "Rust",
    "Ruby", "PHP", "Kotlin", "Dart", "Scala", "Perl", "R", "Objective-C", "Haskell", "Lua", "Shell Scripting",
    "HTML", "CSS", "Sass", "Less", "React", "Vue.js", "Angular", "Svelte", "Next.js", "Nuxt.js",
    "Gatsby", "Bootstrap", "Tailwind CSS", "Material UI", "Chakra UI", "jQuery",
    "Node.js", "Express.js", "NestJS", "Django", "Flask", "FastAPI", "Spring Boot", "Ruby on Rails",
    "ASP.NET Core", "Laravel", "Phoenix (Elixir)", "Go Fiber", "Koa.js", "Actix (Rust)",
    "MySQL", "PostgreSQL", "SQLite", "MariaDB", "Microsoft SQL Server", "Oracle Database",
    "MongoDB", "Firebase Firestore", "Cassandra", "CouchDB", "DynamoDB", "Redis", "Neo4j", "InfluxDB",
    "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "GitHub Actions", "CircleCI",
    "AWS", "Azure", "Google Cloud Platform", "Heroku", "Vercel", "Netlify", "DigitalOcean", "Cloudflare",
    "GraphQL", "REST API", "gRPC", "WebSockets", "Kafka", "RabbitMQ", "NATS Streaming", "Redis Streams",
    "Machine Learning", "Data Science", "Deep Learning", "TensorFlow", "Keras", "PyTorch", "OpenCV",
    "Pandas", "NumPy", "Scikit-Learn", "Matplotlib", "Seaborn", "Hugging Face Transformers",
    "Apache Hadoop", "Apache Spark", "Apache Flink", "Snowflake", "Google BigQuery",
    "ClickHouse", "Dask", "Presto", "Redshift", "Elasticsearch", "Grafana", "Tableau", "Power BI",
    "React Native", "Flutter", "Xamarin", "Ionic", "Cordova", "Unity", "Unreal Engine",
    "Solidity", "Ethereum", "Web3.js", "Hardhat", "Truffle", "IPFS", "Polkadot",
    "OWASP", "Burp Suite", "Metasploit", "Wireshark", "Snort", "Suricata", "Nmap", "Splunk", "SIEM",
    "Selenium", "Cypress", "Playwright", "Jest", "Mocha", "Chai", "PyTest", "JUnit", "TestNG", "Cucumber",
    "Git", "GitHub", "GitLab", "Bitbucket", "Linux", "Bash", "PowerShell", "WebAssembly (WASM)",
    "Figma", "Adobe XD", "Postman", "Swagger", "Insomnia", "Vim", "Emacs", "VS Code", "JetBrains IntelliJ"
])  # keep your long skills list here

def extract_text(file):
    if file.filename.endswith('.pdf'):
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif file.filename.endswith('.docx'):
        return docx2txt.process(file)
    return ""

def extract_name(text):
    top_lines = text.strip().split('\n')[:10]
    exclude_keywords = ["institute", "university", "college", "technology", "school", "engineering", "jun", "may", "april", "aug", "sept", "2020", "2021", "2022", "2023", "2024", "2025"]

    doc = nlp("\n".join(top_lines))
    for ent in doc.ents:
        if ent.label_ == "PERSON" and not any(word in ent.text.lower() for word in exclude_keywords):
            return ent.text.strip()

    name_pattern = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")
    for line in top_lines:
        if any(word in line.lower() for word in exclude_keywords):
            continue
        match = name_pattern.search(line)
        if match:
            return match.group()

    return "Name not found"

def extract_email(text):
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return match.group() if match else "Email not found"

def extract_phone(text):
    match = re.search(r'\b(?:\+91[-\s]?)?[6-9]\d{9}\b', text)
    return match.group() if match else "Phone not found"

def extract_skills(text):
    found_skills = set()
    text_words = set(word.strip(".,()[]{}").lower() for word in text.split())
    for skill in SKILLS_LIST:
        if skill.lower() in text_words:
            found_skills.add(skill)
    missing_skills = sorted(SKILLS_LIST - found_skills)
    return sorted(found_skills), missing_skills

@app.route('/', methods=['GET', 'POST'])
def index():
    name = email = phone = None
    matched_skills = []
    missing_skills = []
    ats_score = 0

    if request.method == 'POST':
        resume = request.files['resume']
        job_desc = request.form['job_description']
        if resume and job_desc:
            resume_text = extract_text(resume)
            name = extract_name(resume_text)
            email = extract_email(resume_text)
            phone = extract_phone(resume_text)

            resume_skills, _ = extract_skills(resume_text)
            jd_skills, _ = extract_skills(job_desc)

            matched_skills = sorted(set(resume_skills).intersection(jd_skills))
            missing_skills = sorted(set(jd_skills) - set(resume_skills))

            # ✅ ATS score calculation
            total_skills = len(jd_skills)
            if total_skills > 0:
                ats_score = round((len(matched_skills) / total_skills) * 100, 2)

            # ✅ Insert into MySQL
            sql = "INSERT INTO candidates (name, email, phone, ats_score) VALUES (%s, %s, %s, %s)"
            values = (name, email, phone, ats_score)
            cursor.execute(sql, values)
            conn.commit()

    return render_template(
        'index.html',
        name=name,
        email=email,
        phone=phone,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        ats_score=ats_score
    )

if __name__ == '__main__':
    app.run(debug=True)
