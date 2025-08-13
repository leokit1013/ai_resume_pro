from import_python_packages import *

st.set_page_config(page_title="Check And Fix Against JD", layout="wide")


if "token" not in st.session_state:
    st.switch_page("login.py")

res = requests.post(f"{BACKEND_URL}/validate-token", json={"token": st.session_state["token"]})
if res.status_code != 200:
    st.switch_page("login.py")
    
# hide navbar and footer
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

if "email" not in st.session_state:
    st.warning("Please login to access this page.")
    st.switch_page("app.py")

if st.session_state["usage_count"] >= 50 and not st.session_state["subscribed"]:
    st.warning("You've exceeded your free limit.")
    if st.button("Go to Payment Page"):
        st.switch_page("pages/payment_page.py")
    st.stop()

# Call update once only
if "used_this_tool" not in st.session_state:
    update_usage(st.session_state["email"])
    st.session_state["usage_count"] += 1
    st.session_state["used_this_tool"] = True


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file or environment variables.")
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel(
    'gemini-1.5-flash-8b-001',
    generation_config={
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
)

def detect_language(text):
    return detect(text)



def download_resume_pdf(resume_text):
    """Generate a PDF from resume text and make it downloadable."""
    buffer = io.BytesIO()

    # Create PDF with ReportLab
    c = canvas.Canvas(buffer, pagesize=A4)
    text_object = c.beginText(40, 800)  # Starting position

    for line in resume_text.split("\n"):
        text_object.textLine(line)
    c.drawText(text_object)
    c.showPage()
    c.save()

    buffer.seek(0)

    # Streamlit download button
    st.download_button(
        label="📄 Download PDF",
        data=buffer,
        file_name="resume.pdf",
        mime="application/pdf"
    )


def summarize_with_gemini(prompt: str) -> str | None:
    """
    Sends a prompt to the Gemini model and returns the generated text.
    """
    try:
        response = model.generate_content(prompt)
        return response.text if response and response.text else None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None
    
def generate_resume_suggestions(resume_text: str, job_description: str) -> list:
    """
    Compares a resume with a job description and returns actionable improvement suggestions.
    """
    if not resume_text or not job_description:
        return []

    # Construct prompt for Gemini
    prompt = f"""
    Compare the following resume with this job description.

    Job Description:
    {job_description}

    Resume:
    {resume_text}

    Provide a list of specific, actionable suggestions to improve the resume
    so that it aligns better with the job description. Format each suggestion as a bullet starting with '- '.
    """

    # Generate suggestions via Gemini
    suggestions_text = summarize_with_gemini(prompt)
    if not suggestions_text:
        return []

    # Extract individual suggestions from bullets
    suggestions = re.findall(r"- (.+)", suggestions_text)
    return suggestions


def download_resume_docx(resume_text):
    """Generate a DOCX from resume text and make it downloadable."""
    buffer = io.BytesIO()

    # Create DOCX with python-docx
    doc = Document()
    for line in resume_text.split("\n"):
        doc.add_paragraph(line)
    doc.save(buffer)

    buffer.seek(0)

    # Streamlit download button
    st.download_button(
        label="📄 Download DOCX",
        data=buffer,
        file_name="resume.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

def create_pdf(content):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    for line in content.splitlines():
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(40, y, line.strip())
        y -= 15

    c.save()
    buffer.seek(0)
    return buffer


def read_image(file, lang):
    image = Image.open(file)
    image_np = np.array(image)
    reader = easyocr.Reader([lang, 'en'], gpu=False)
    result = reader.readtext(image_np, detail=0)
    return ' '.join(result)

def extract_text_from_file(file):
    try:
        if file.name.endswith(".pdf"):
            text = ""
            pdf_bytes = file.read()
            if not pdf_bytes:
                st.error("Error: Uploaded PDF is empty.")
                return None
            try:
                reader = PdfReader(BytesIO(pdf_bytes))
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n\n"
            except:
                pass
            if not text:
                try:
                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    for page in doc:
                        t = page.get_text("text")
                        if t:
                            text += t + "\n\n"
                except:
                    pass
            if not text:
                try:
                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    for page in doc:
                        pix = page.get_pixmap()
                        img_bytes = pix.tobytes("png")
                        lang = detect_language(read_image(BytesIO(img_bytes), 'en'))
                        text += read_image(BytesIO(img_bytes), lang) + "\n\n"
                except Exception as e:
                    st.error(f"OCR failed: {e}")
                    return None
            return text

        elif file.name.endswith(".txt"):
            return file.read().decode("utf-8")

        elif file.name.endswith(".docx"):
            doc = Document(file)
            return "\n".join(p.text for p in doc.paragraphs)

        elif file.name.endswith((".jpg", ".jpeg", ".png")):
            temp_text = read_image(file, 'en')
            lang = detect_language(temp_text)
            return read_image(file, lang)

        else:
            st.error("Unsupported file type.")
            return None

    except Exception as e:
        st.error(f"Text extraction failed: {e}")
        return None


        
        
def main():

    # ✅ Persistent state initialization at the very top
    if "screen" not in st.session_state:
        st.session_state.screen = "main"
    if "resume_text" not in st.session_state:
        st.session_state.resume_text = ""
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = []
    if "scores" not in st.session_state:
        st.session_state.scores = {}
    if "job_desc" not in st.session_state:
        st.session_state.job_desc = ""
        
    st.markdown("## 🧠 AI Resume Pro")
    st.markdown("Optimize your resume for your dream job in just a few steps!")

    print(f"Current screen: {st.session_state.screen}")  # Debugging output
    if st.session_state.screen == "main":
        show_main_screen()
    elif st.session_state.screen == "fix":
        show_fix_screen()

def show_main_screen():

    st.markdown(
        f"<h1 style='margin-top:0;'>Hi, Tanveer! Let's boost your match score 🚀</h1>"
        "<p style='font-size:16px; color:#555;'>Paste the job description, upload your resume, and see exactly what to fix.</p>",
        unsafe_allow_html=True
    )

    # Step 1: Job Description
    st.markdown("### 1️⃣ Paste Job Description")
    job_input = st.text_area(
        placeholder="Paste your job description or job link here...",
        label="Job Description Input",
        height=120
    )

    # Step 2: Upload Resume
    st.markdown("### 2️⃣ Upload Your Resume")
    file = st.file_uploader(
        "Drop your resume here (PDF, DOCX, TXT, XML, Image)",
        type=["pdf", "txt", "docx", "xml", "jpg", "jpeg", "png"],
        accept_multiple_files=False
    )

    # Step 3: Check Match
    st.markdown("### 3️⃣ Check Your Match Score")
    run_check = st.button("🚀 Check My Resume", use_container_width=True)

    if run_check:
        if not job_input.strip():
            st.warning("⚠️ Please enter the job description.")
            return
        if not file:
            st.warning("⚠️ Please upload a resume file.")
            return

        resume_text = extract_text_from_file(file)
        st.session_state.resume_text = resume_text  # Store for live editing
        st.session_state.job_desc = job_input.strip()

        # Candidate-focused prompt
        default_prompt = """
        You are an expert career coach and resume optimization specialist.

        Your task: Compare the candidate's resume to the provided job description
        and provide feedback to improve their chances.

        Job Description:
        {requirement}

        Candidate Resume:
        {text}

        Output format (STRICTLY follow this):

        ```
        Overall Score: XX
        Skills Score: XX
        Experience Score: XX
        ATS Compatibility Score: XX
        Recommendations:
        - Add missing keywords: Keyword1, Keyword2
        - Include the job title in your summary
        - Mention leadership in the experience section
        ```
        """.strip()

        final_prompt = default_prompt.format(requirement=job_input.strip(), text=resume_text.strip())
        with st.spinner("🔍 Analyzing resume..."):
            summary = summarize_with_gemini(final_prompt)

        if summary:
            st.session_state.summary = summary  # <-- store summary in session state
        else:
            st.session_state.summary = None

    if st.session_state.get("summary"):
        summary = st.session_state.summary

        # Parse scores
        st.session_state.scores["overall"] = int(re.search(r"Overall Score:\s*(\d+)", summary).group(1))
        st.session_state.scores["skills"] = int(re.search(r"Skills Score:\s*(\d+)", summary).group(1))
        st.session_state.scores["experience"] = int(re.search(r"Experience Score:\s*(\d+)", summary).group(1))
        st.session_state.scores["ats"] = int(re.search(r"ATS Compatibility Score:\s*(\d+)", summary).group(1))
        st.session_state.recommendations = re.findall(r"- (.+)", summary)

        st.session_state.all_scores = {
            "overall": st.session_state.scores["overall"],
            "sections": {
                "Skills": st.session_state.scores["skills"],
                "Experience": st.session_state.scores["experience"],
                "ATS Compatibility": st.session_state.scores["ats"] 
            }
        }
        # Show scores
        overall_score = st.session_state.scores["overall"]
        st.subheader("📊 Match Score")
        st.markdown(
            f"<h1 style='color:#00BFA5;text-align:center;'>{overall_score}</h1><p style='text-align:center;'>Resume Match Score</p>",
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Skills",  st.session_state.scores["skills"])
        col2.metric("Experience", st.session_state.scores["experience"])
        col3.metric("ATS Compatibility", st.session_state.scores["ats"])

        # Show recommendations
        st.markdown("### 🛠 Recommendations")
        for rec in st.session_state.recommendations:
            st.markdown(f"- {rec}")
            print(f"Suggestion: {rec}")

        # Fix Now button will always be visible after results
        if st.button("Fix Now", type="primary", key="fix_now_btn"):
            st.write("DEBUG: Fix Now button clicked")
            print("before click", st.session_state.get("screen"))
            st.session_state.screen = "fix"
            print("after click", st.session_state.screen)
            st.rerun()

    elif run_check:  # only show error if check was clicked and failed
        st.error("❌ Could not generate a summary.")



def show_fix_screen():
    st.write("DEBUG: Current screen =", st.session_state.screen)  # Optional debug

    st.title("🛠 Resume Fix & Suggestions")

    # Ensure required state exists
    if "resume_text" not in st.session_state:
        st.warning("No resume data found. Redirecting to dashboard...")
        st.session_state.screen = "main"
        st.rerun()

    # ---- TOP BAR ----
    col1, col2, col3 = st.columns([1, 6, 1])
    with col3:
        if st.button("🏠 Back to Dashboard"):
            for key in ["resume_text", "recommendations", "scores"]:
                st.session_state.pop(key, None)
            st.session_state.screen = "main"
            st.rerun()

    # ---- SCORES SECTION ----
    st.subheader("📊 ATS Score Overview")
    if "scores" in st.session_state and st.session_state.scores:
        ats_score = st.session_state.scores.get("overall", 0)
        st.progress(ats_score / 100)
        st.write(f"**Overall ATS Score:** {ats_score}%")

        # Section-wise breakdown
        st.write("### Section-wise Scores")
        for section, score in st.session_state.all_scores.get("sections", {}).items():
            st.write(f"- **{section}:** {score}%")
            st.progress(score / 100)
    else:
        st.info("Score data not available. Please recheck the score.")

    st.markdown("---")

    # ---- RESUME PREVIEW ----
    st.subheader("📄 Current Resume Preview")
    st.text_area("Resume Text", st.session_state.resume_text, height=300, key="resume_preview")

    # Download buttons
    cols = st.columns(2)  # 2 equal columns

    with cols[0]:
        if st.button("⬇ Download as PDF", use_container_width=True):
            download_resume_pdf(st.session_state.resume_text)

    with cols[1]:
        if st.button("⬇ Download as DOCX", use_container_width=True):
            download_resume_docx(st.session_state.resume_text)

    st.markdown("---")

    # ---- SUGGESTIONS SECTION ----
    st.subheader("💡 Suggestions")
    resume_text = st.session_state.get("resume_text", "")
    job_desc = st.session_state.get("job_desc", "")

    if resume_text and job_desc:
        st.session_state.recommendations = generate_resume_suggestions(resume_text, job_desc)

    if "recommendations" in st.session_state and st.session_state.recommendations:
        for i, rec in enumerate(st.session_state.recommendations):
            st.markdown(f"**{i+1}.** {rec}")

            if st.button(f"Apply Suggestion {i+1}", key=f"apply_{i}"):
                st.session_state.resume_text = apply_suggestion(st.session_state.resume_text, rec)
                st.session_state.screen = "fix"
                st.rerun()
 
    else:
        st.info("No suggestions available.")

    st.markdown("---")

    # ---- ACTIONS ----
    if st.button("🔄 Recheck Score"):
        st.session_state.scores = score_resume(st.session_state.resume_text)
        st.session_state.screen = "main"
        st.rerun()


def apply_suggestion(resume_text, suggestion):
    """
    Applies suggestion to resume text:
    - Adds missing keywords
    - Includes job title
    - Mentions leadership
    """
    updated_text = resume_text

    # Add keywords
    keyword_match = re.search(r"Add missing keywords?:\s*(.+)", suggestion, re.IGNORECASE)
    if keyword_match:
        keywords = keyword_match.group(1).split(",")
        updated_text += "\n\nSkills:\n" + ", ".join([kw.strip() for kw in keywords])

    # Include job title
    if "Include the job title" in suggestion:
        updated_text = f"Professional Summary:\n[JOB TITLE HERE] — " + updated_text

    # Mention leadership
    if "leadership" in suggestion.lower():
        updated_text += "\n\nExperience:\n- Demonstrated leadership in managing projects and teams."

    return updated_text


def score_resume(resume_text):
    """
    Dummy scoring logic for now — replace with your AI/ML scoring call.
    Returns a dict with different evaluation scores.
    """
    score = len(resume_text) % 100  # example: just a fake number for now
    return {
        "ATS Match Score": score,
        "Keyword Coverage": min(100, score + 10),
        "Readability": min(100, score + 5)
    }




if __name__ == "__main__":
    main()
