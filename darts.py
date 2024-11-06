import streamlit as st
import openai
import fitz  # PyMuPDF for PDF text extraction
from docx import Document  # python-docx for Word files
import re  # Import regex for pattern matching

# Set OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# List of generic Darts (color-based) to exclude
generic_darts = ["Red", "Green", "Blue", "Yellow", "Purple", "Orange", "Pink", "Beige", "Silver", "Maroon"]

# Helper Functions
def extract_text(document):
    """Extract text from PDF or Word documents."""
    if document.type == "application/pdf":
        return extract_text_from_pdf(document)
    elif document.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_word(document)
    else:
        return document.getvalue().decode("utf-8")

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF using PyMuPDF."""
    text = ""
    try:
        with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    except Exception:
        text = ""
    return text

def extract_text_from_word(word_file):
    """Extract text from Word document using python-docx."""
    try:
        doc = Document(word_file)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    except Exception:
        return ""

# Summarize brand elements with an optional manual entry
def summarize_brand_style(document=None, manual_input=None):
    if document:
        content = extract_text(document)
    elif manual_input:
        content = manual_input
    else:
        return {}

    # Create prompt to extract brand details
    prompt = (
        f"Extract the brand voice, brand positioning, and unique value propositions from the following brand guidelines. "
        f"Structure the response as follows:\n\n"
        f"- Brand Voice:\n- Brand Positioning:\n- Unique Value Propositions:\n\n"
        f"Brand Guidelines Content:\n\n{content}"
    )
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    details_text = response.choices[0].message.content.strip()

    # Parse and clean up output
    brand_elements = {
        "Brand Voice": "",
        "Brand Positioning": "",
        "Unique Value Propositions": ""
    }
    if "Brand Voice:" in details_text:
        brand_elements["Brand Voice"] = details_text.split("Brand Voice:", 1)[1].split("Brand Positioning:", 1)[0].strip().strip("*-")
    if "Brand Positioning:" in details_text:
        brand_elements["Brand Positioning"] = details_text.split("Brand Positioning:", 1)[1].split("Unique Value Propositions:", 1)[0].strip().strip("*-")
    if "Unique Value Propositions:" in details_text:
        brand_elements["Unique Value Propositions"] = details_text.split("Unique Value Propositions:", 1)[1].strip().strip("*-")

    # Ensure formatting does not include extra symbols or repeated sections
    for key, value in brand_elements.items():
        if not value or value.lower() == "no information available.":
            brand_elements[key] = "No information available."

    return {key: remove_bullets(value) for key, value in brand_elements.items()}

def remove_bullets(text):
    """Remove bullet points, numbered lists, or special characters from the beginning of each line."""
    cleaned_text = '\n'.join([re.sub(r'^\d+\.\s*|^[\-*•]\s*', '', line).strip() for line in text.splitlines() if line.strip()])
    return cleaned_text.replace('*', '')

def extract_dart_names(document):
    """Extract only the names of specific Darts (excluding generic and color-based ones) from the document."""
    content = extract_text(document)
    prompt = (
        f"List only the names of each Dart mentioned in the following document. Do not include any descriptions, "
        f"characteristics, or psychographic drivers, just list the Dart names as a numbered list:\n\n{content}"
    )
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    dart_names = [
        line.strip() for line in response.choices[0].message.content.splitlines()
        if line.strip() and all(color not in line for color in generic_darts)
    ]
    return dart_names

def extract_dart_details(document, dart_name):
    """For each Dart name, extract characteristics and psychographic drivers."""
    content = extract_text(document)
    prompt = (
        f"Provide only the characteristics and psychographic drivers for the Dart '{dart_name}' based on the following "
        f"document content. Use this format:\n\n"
        f"- Characteristics: (list characteristics here)\n"
        f"- Psychographic Drivers: (list psychographic drivers here)\n\n"
        f"Document content:\n\n{content}"
    )
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    details_text = response.choices[0].message.content.strip()
    characteristics = ""
    psychographic_drivers = ""
    
    if "Characteristics:" in details_text:
        characteristics = details_text.split("Characteristics:", 1)[1].split("Psychographic Drivers:", 1)[0].strip().strip("*-")
    if "Psychographic Drivers:" in details_text:
        psychographic_drivers = details_text.split("Psychographic Drivers:", 1)[1].strip().strip("*-")
    
    return {
        "Characteristics": remove_bullets(characteristics),
        "Psychographic Drivers": remove_bullets(psychographic_drivers)
    }

def extract_all_darts(document):
    """Combine functions to extract all specific Darts and their details one by one."""
    darts = {}
    dart_names = extract_dart_names(document)
    
    for dart_name in dart_names:
        dart_details = extract_dart_details(document, dart_name)
        darts[dart_name] = dart_details
    
    return darts

# Modify `generate_content_for_dart` to incorporate brand elements in the content strategy
def generate_content_for_dart(content, brand_summary, dart_characteristics):
    """Generate content tailored for a specific Dart, considering brand guidelines."""
    
    brand_voice = brand_summary["Brand Voice"]
    brand_positioning = brand_summary["Brand Positioning"]
    unique_value_propositions = brand_summary["Unique Value Propositions"]
    
    prompt = (
        f"Rewrite the following content to appeal to an audience with these characteristics: {dart_characteristics}. "
        f"Ensure the content reflects the brand voice, positioning, and unique value propositions as described:\n\n"
        f"- Brand Voice: {brand_voice}\n"
        f"- Brand Positioning: {brand_positioning}\n"
        f"- Unique Value Propositions: {unique_value_propositions}\n\n"
        f"Here is the original content:\n\n{content}"
    )
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return remove_bullets(response.choices[0].message.content.strip())

def download_text_file(file_name, content):
    """Create a downloadable link for a text file with the given content."""
    st.download_button(
        label=f"Download {file_name}",
        data=content,
        file_name=file_name,
        mime="text/plain"
    )

# Main Script
st.title("Email Content Personalization with Darts")

# Step 1: Upload or manually enter client’s brand and style guide
st.subheader("Client's Brand and Style Guide")
brand_style_guide = st.file_uploader("Upload a PDF or Word document (optional)", type=["pdf", "docx", "txt"])
manual_brand_input = st.text_area("Or, enter brand voice, positioning, and unique value propositions manually if no file is uploaded:")

if brand_style_guide or manual_brand_input:
    brand_summary = summarize_brand_style(brand_style_guide, manual_brand_input)
    if brand_summary:
        st.write("**Brand Voice:**")
        st.write(brand_summary["Brand Voice"])
        st.write("**Brand Positioning:**")
        st.write(brand_summary["Brand Positioning"])
        st.write("**Unique Value Propositions:**")
        st.write(brand_summary["Unique Value Propositions"])

# Step 2: Upload client's Darts document
st.subheader("Client's Darts Document")
darts_doc = st.file_uploader("Upload Darts document", type=["pdf", "docx", "txt"])

if darts_doc:
    darts = extract_all_darts(darts_doc)
    st.write("**Client's Darts:**")
    for dart, details in darts.items():
        if details["Characteristics"] != "No information available." or details["Psychographic Drivers"] != "No information available.":
            st.write(f"**{dart}**")
            st.write(f"Characteristics:\n{details['Characteristics']}")
            st.write(f"Psychographic Drivers:\n{details['Psychographic Drivers']}")

# Step 3: Upload content for Dart-specific personalization
st.subheader("Content Personalization for All Darts")
content_doc = st.file_uploader("Upload sample content (e.g., an email)", type=["pdf", "docx", "txt"])

if content_doc and darts:
    original_content = extract_text(content_doc)
    st.write("**Original Content:**")
    st.write(original_content)

    # Generate Dart-specific content and provide download links
    st.subheader("Generated Content for Each Dart")
    for dart, details in darts.items():
        dart_characteristics = details["Characteristics"]
        generated_content = generate_content_for_dart(original_content, brand_summary, dart_characteristics)
        st.write(f"**Content for Dart - {dart}:**")
        st.write(generated_content)

        # Create a downloadable link for each Dart's content
        file_name = f"{dart.replace(' ', '_')}_content.txt"
        download_text_file(file_name, generated_content)

# Step 4: User revision input for generated content
st.subheader("User Revision Input")
revision_instructions = st.text_area("Specify the revisions to be made:")
content_to_revise = st.text_area("Paste the content to be revised here:", height=200)

if content_to_revise:
    revised_content = f"Instructions for revision: {revision_instructions}\n\nContent to revise:\n{remove_bullets(content_to_revise)}"
    st.write("**Revised Content Preview:**")
    st.write(revised_content)

    # Create a downloadable link for the revised content
    download_text_file("revised_content.txt", revised_content)
