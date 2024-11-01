import streamlit as st
import openai
import fitz  # PyMuPDF for PDF text extraction
from docx import Document  # python-docx for Word files

# Set OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# List of generic Darts (color-based) to exclude
generic_darts = ["Red", "Green", "Blue", "Yellow", "Purple", "Orange", "Pink", "Beige", "Silver", "Maroon"]

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
    try:
        with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        st.error("Error reading PDF file. Please check the file and try again.")
        text = ""
    return text

def extract_text_from_word(word_file):
    """Extract text from Word document using python-docx."""
    try:
        doc = Document(word_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        st.error("Error reading Word file. Please check the file and try again.")
        text = ""
    return text

# Updated `summarize_brand_style` to extract key brand elements
def summarize_brand_style(document):
    """Extracts brand voice, positioning, and unique value propositions from the brand guidelines document."""
    content = extract_text(document)
    
    # Ask the model to extract specific brand elements
    prompt = (
        f"Extract the brand voice, brand positioning, and unique value propositions from the following brand guidelines. "
        f"Structure the response as follows:\n\n"
        f"- Brand Voice: (list voice characteristics)\n"
        f"- Brand Positioning: (describe the positioning)\n"
        f"- Unique Value Propositions: (list value propositions)\n\n"
        f"Brand Guidelines Content:\n\n{content}"
    )
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    details_text = response.choices[0].message.content.strip()
    
    # Parsing brand elements from the response
    brand_voice = ""
    brand_positioning = ""
    unique_value_propositions = ""
    
    if "Brand Voice:" in details_text:
        brand_voice = details_text.split("Brand Voice:", 1)[1].split("Brand Positioning:", 1)[0].strip()
    if "Brand Positioning:" in details_text:
        brand_positioning = details_text.split("Brand Positioning:", 1)[1].split("Unique Value Propositions:", 1)[0].strip()
    if "Unique Value Propositions:" in details_text:
        unique_value_propositions = details_text.split("Unique Value Propositions:", 1)[1].strip()
    
    return {
        "Brand Voice": brand_voice,
        "Brand Positioning": brand_positioning,
        "Unique Value Propositions": unique_value_propositions
    }

def extract_dart_names(document):
    """First, extract only the names of specific Darts (excluding generic ones) from the document."""
    content = extract_text(document)
    prompt = (
        f"List only the names of each Dart mentioned in the following document. Do not include any descriptions, "
        f"characteristics, or psychographic drivers, just list the Dart names as a numbered list:\n\n{content}"
    )
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Split and clean each line to extract Dart names, then filter out generic names
    dart_names = [
        line.strip() for line in response.choices[0].message.content.splitlines()
        if line.strip() and line.strip() not in generic_darts
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
    
    # Extract characteristics and psychographic drivers from the response
    details_text = response.choices[0].message.content.strip()
    characteristics = ""
    psychographic_drivers = ""
    
    if "Characteristics:" in details_text:
        characteristics = details_text.split("Characteristics:", 1)[1].split("Psychographic Drivers:", 1)[0].strip()
    if "Psychographic Drivers:" in details_text:
        psychographic_drivers = details_text.split("Psychographic Drivers:", 1)[1].strip()
    
    return {"Characteristics": characteristics, "Psychographic Drivers": psychographic_drivers}

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
    
    # Incorporate extracted brand elements into the content generation strategy
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
    
    return response.choices[0].message.content.strip()

# Main Script
st.title("Email Content Personalization with Darts")
st.write("Generate tailored email content based on specific Darts (audience profiles) and client brand guidelines.")

# Step 1: Upload and summarize client’s brand and style guide
st.subheader("Upload Client's Brand and Style Guide")
brand_style_guide = st.file_uploader("Choose a PDF or Word document", type=["pdf", "docx", "txt"])

if brand_style_guide is not None:
    brand_summary = summarize_brand_style(brand_style_guide)
    st.write("**Brand Voice:**")
    st.write(brand_summary["Brand Voice"])
    st.write("**Brand Positioning:**")
    st.write(brand_summary["Brand Positioning"])
    st.write("**Unique Value Propositions:**")
    st.write(brand_summary["Unique Value Propositions"])

# Step 2: Upload and display client’s Darts document
st.subheader("Upload Client's Darts Document")
darts_doc = st.file_uploader("Upload Darts document", type=["pdf", "docx", "txt"])

if darts_doc is not None:
    darts = extract_all_darts(darts_doc)
    st.write("**Client's Darts:**")
    for dart, details in darts.items():
        st.write(f"**{dart}**")
        st.write(f"- **Characteristics**: {details['Characteristics']}")
        st.write(f"- **Psychographic Drivers**: {details['Psychographic Drivers']}")

# Step 3: Upload content document and select Dart for personalization
st.subheader("Upload Content for Dart-Specific Personalization")
content_doc = st.file_uploader("Upload content (usually an email)", type=["pdf", "docx", "txt"])

if content_doc is not None and darts:
    selected_dart = st.radio("Select the Dart this content applies to:", list(darts.keys()))
    other_darts = [dart for dart in darts.keys() if dart != selected_dart]

    # Show original content
    original_content = extract_text(content_doc)
    st.write("**Original Content:**")
    st.write(original_content)

    # Generate content for other Darts
    st.subheader("Generated Content for Other Darts")
    for dart in other_darts:
        dart_characteristics = darts[dart]["Characteristics"]
        generated_content = generate_content_for_dart(original_content, brand_summary, dart_characteristics)
        
        st.write(f"**Content for Dart - {dart}:**")
        st.write(generated_content)
