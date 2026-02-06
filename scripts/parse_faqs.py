import os
import json
import glob
import docx  # For .docx files
import fitz  # PyMuPDF for .pdf files

DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'faq_docs')

# Output file
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'parsed_faqs.json')


def parse_docx(file_path):
    """
    Parses a .docx file, extracting text paragraph by paragraph.
    Each non-empty paragraph becomes a separate JSON entry.
    """
    print(f"Parsing DOCX: {os.path.basename(file_path)}")
    data = []
    try:
        doc = docx.Document(file_path)

        # Create a new entry for each one.
        for para in doc.paragraphs:
            text = para.text.strip()

            # Clean up text: remove excessive whitespace and newlines
            cleaned_text = ' '.join(text.split())

            # Only add non-empty strings that have meaningful content
            if cleaned_text and len(cleaned_text) > 10:  # Avoid short/empty lines
                data.append({
                    "source": os.path.basename(file_path),
                    "content": cleaned_text
                })

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    return data


def parse_pdf(file_path):
    """
    Parses a .pdf file using PyMuPDF (fitz).
    It extracts text "blocks" to preserve paragraph structure.
    Each block becomes a separate JSON entry.
    """
    print(f"Parsing PDF: {os.path.basename(file_path)}")
    data = []
    try:
        doc = fitz.open(file_path)

        # Iterate through each page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            blocks = page.get_text("blocks")

            for b in blocks:
                text = b[4]  # The 5th item in the tuple is the text content

                # Clean up text: remove excessive whitespace and newlines
                cleaned_text = ' '.join(text.split())

                # Only add non-empty strings that have meaningful content
                if cleaned_text and len(cleaned_text) > 10:  # Avoid headers/footers
                    data.append({
                        "source": os.path.basename(file_path),
                        "content": cleaned_text
                    })

        doc.close()
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    return data


def main():
    """
    Main function to find all documents, parse them,
    and save the combined content.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_files = []
    supported_extensions = ['*.docx', '*.pdf']
    for ext in supported_extensions:
        all_files.extend(glob.glob(os.path.join(DOCS_DIR, ext)))

    if not all_files:
        print(f"No documents (.docx, .pdf) found in {DOCS_DIR}")
        # Create an empty file to prevent errors downstream
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return

    print(f"Found {len(all_files)} documents to parse...")
    all_data = []

    for file_path in all_files:
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.docx':
            all_data.extend(parse_docx(file_path))
        elif file_ext == '.pdf':
            all_data.extend(parse_pdf(file_path))

    # Save the combined data to the output file
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Error writing to JSON file {OUTPUT_FILE}: {e}")
        return

    print(f"\nSuccessfully parsed and processed {len(all_data)} content block(s).")
    print(f"Data saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

