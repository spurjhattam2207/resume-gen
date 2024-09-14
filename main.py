from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import shutil
import os
import pdfplumber
import google.generativeai as genai
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()
API_KEY = os.getenv('API_KEY')

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

UPLOAD_DIR = "uploads"
RESUME_DIR = "views"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
if not os.path.exists(RESUME_DIR):
    os.makedirs(RESUME_DIR)


@app.get("/")
def read_root():
    return FileResponse("views/index.html")


@app.post("/upload")
async def upload_pdf(pdf: UploadFile = File(...)):
    try:
        file_location = f"{UPLOAD_DIR}/{pdf.filename}"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(pdf.file, file_object)

        extracted_content = extract_text_from_pdf(file_location)

        prompt = f"""
        Generate an HTML resume for the following details, following this structure:
        - Name in <h1> or <h2> and left-aligned.
        - A line like a footer to separate sections.
        - Each section header will have a footer above and below it.
        - The content's important words should be bold.
        - Education section:
          - The section header should be bold and smaller than the name.
          - The alma mater should be in bold, while grades and other content should not be bold.
        - Achievements section:
          - The section header should be bold.
          - Each achievement should have a subheading (name of the award/achievement) in bold, followed by a half-line description in normal text on the same line.
          - Bullet each achievement.
        - Experience section:
          - The section header should be bold.
          - Each job/experience should have a subheading (company/role) in bold.
          - Bullet points for each responsibility/accomplishment, with each point as a complete line.
        - Projects section:
          - Similar to the experience section.
          - Subheading for each project in bold, followed by bullet points.
          - If no projects found, do not include this section.

        Please don't add any extra content apart from the pdf data, you may use the description from the pdf wherever required. Also, add styling as well for grayscale-blue theme and sans-serif font.

        Here's the LinkedIn content to generate the resume from: {extracted_content}.
        """

        result = model.generate_content(prompt)
        resume_html = result.text

        resume_path = os.path.join(RESUME_DIR, 'resume.html')
        with open(resume_path, "w") as html_file:
            html_file.write(resume_html)

        return FileResponse(resume_path)

    except Exception as e:
        return {"error": str(e)}

    finally:
        if os.path.exists(file_location):
            os.remove(file_location)


@app.get("/resume")
def get_resume():
    return FileResponse("views/resume.html")


def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text