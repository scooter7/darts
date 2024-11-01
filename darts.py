import streamlit as st
import openai
import fitz  # PyMuPDF
from docx import Document  # python-docx

# Set OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Helper Functions
def extract_text(document):
    """Extract text from PDF or Word documents."""
    if document.type == "application/pdf":
        text = extract_text_from_pdf(document)
    elif document.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = extract_text_from_word(document)
    else:
        text = document.getvalue().decode("utf-8")
    return text

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using PyMuPDF."""
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_word(word_file):
    """Extract text from Word document using python-docx."""
    doc = Document(word_file)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text

def summarize_brand_style(document):
    # Extract and summarize brand and style guidelines
    content = extract_text(document)
    prompt = f"Summarize the brand and style guidelines from the following document content:\n\n{content}"
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def extract_darts(document):
    # Extract Darts from the uploaded document
    content = extract_text(document)
    prompt = f"Identify and list the Darts described in the following document:\n\n{content}"
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    dart_text = response.choices[0].message.content.strip()
    # Parse the response into a dictionary format
    darts = {line.split(":")[0].strip(): line.split(":")[1].strip() for line in dart_text.splitlines() if ":" in line}
    return darts

def generate_content_for_dart(content, brand_summary, dart_characteristics):
    # Use OpenAI to personalize content based on brand and dart characteristics
    prompt = (f"Rewrite the following content to appeal to an audience with these characteristics: "
              f"{dart_characteristics}. Apply the following brand guidelines: {brand_summary}. "
              f"Here is the original content:\n\n{content}")
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# Main Script
st.title("Email Content Personalization with Darts")
st.write("Generate tailored email content based on specific Darts (audience profiles) and client brand guidelines.")

# Upload client’s brand and style guide
st.subheader("Upload Client's Brand and Style Guide")
brand_style_guide = st.file_uploader("Choose a PDF or Word document", type=["pdf", "docx", "txt"])

if brand_style_guide is not None:
    brand_summary = summarize_brand_style(brand_style_guide)
    st.write("**Brand and Style Summary:**")
    st.write(brand_summary)

# Further steps can proceed with this approach for extracting and summarizing content.
