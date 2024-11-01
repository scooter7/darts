import streamlit as st
import openai

# Set OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Helper Functions
def summarize_brand_style(document):
    # Extract and summarize brand and style guidelines
    prompt = f"Summarize the brand and style guidelines from the following document content:\n\n{extract_text(document)}"
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"].strip()

def extract_darts(document):
    # Extract Darts from the uploaded document
    prompt = f"Identify and list the Darts described in the following document:\n\n{extract_text(document)}"
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    dart_text = response.choices[0].message["content"].strip()
    # Parse the response into a dictionary format
    darts = {line.split(":")[0].strip(): line.split(":")[1].strip() for line in dart_text.splitlines() if ":" in line}
    return darts

def extract_text(document):
    # Placeholder function for text extraction logic
    return "Text extracted from the document."

def generate_content_for_dart(content, brand_summary, dart_characteristics):
    # Use OpenAI to personalize content based on brand and dart characteristics
    prompt = (f"Rewrite the following content to appeal to an audience with these characteristics: "
              f"{dart_characteristics}. Apply the following brand guidelines: {brand_summary}. "
              f"Here is the original content:\n\n{content}")
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"].strip()

# Main Script
st.title("Email Content Personalization with Darts")
st.write("Generate tailored email content based on specific Darts (audience profiles) and client brand guidelines.")

best_practices_url = "https://github.com/scooter7/darts/blob/main/So%20you%20want_To%20SHIP.pdf"
st.write(f"[Email Writing Best Practices]({best_practices_url}) - Key points on subject lines, headers, intros, and postscripts")

# Upload client’s brand and style guide
st.subheader("Upload Client's Brand and Style Guide")
brand_style_guide = st.file_uploader("Choose a PDF or Word document", type=["pdf", "docx", "txt"])

if brand_style_guide is not None:
    brand_summary = summarize_brand_style(brand_style_guide)
    st.write("**Brand and Style Summary:**")
    st.write(brand_summary)

# Upload client's Darts document
st.subheader("Upload Client's Darts Document")
darts_doc = st.file_uploader("Upload Darts document", type=["pdf", "docx", "txt"])

if darts_doc is not None:
    darts = extract_darts(darts_doc)
    st.write("**Client's Darts:**")
    for dart, description in darts.items():
        st.write(f"**{dart}**: {description}")

# Upload content and select Dart
st.subheader("Upload Content for Dart-Specific Personalization")
content_doc = st.file_uploader("Upload content (usually an email)", type=["pdf", "docx", "txt"])

if content_doc is not None and darts:
    selected_dart = st.radio("Select the Dart this content applies to:", list(darts.keys()))
    other_darts = [dart for dart in darts.keys() if dart != selected_dart]

    original_content = extract_text(content_doc)
    st.write("**Original Content:**")
    st.write(original_content)

    # Generate content for other Darts
    for dart in other_darts:
        dart_characteristics = darts[dart]
        generated_content = generate_content_for_dart(original_content, brand_summary, dart_characteristics)
        
        st.write(f"**Content for Dart - {dart}:**")
        st.write(generated_content)
