import pdfplumber
import json
import re
import os

PDF_PATH = "database/Merchant-Category-Codes (1).pdf"
OUTPUT_PATH = "database/mcc_master.json"

def extract_mccs_from_pdf(pdf_path):
    mccs = []
    
    # We'll use a regex to identify MCC lines generally appearing in tables
    # MCCs are typically 4 digits.
    # The PDF structure varies, so we'll look for lines starting with 4 digits.
    mcc_pattern = re.compile(r'^(\d{4})\s+(.+)$')
    
    # We also need to capture header/category info if possible, but basic line extraction is key first.
    # Given the complexity of PDFs, we will try to identify table rows provided by pdfplumber
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        return []

    print(f"Extracting from {pdf_path}...")
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract text to find categories or context if needed, 
            # but usually table extraction ensures we get structured data.
            # Let's try simple text processing line by line first as pdf tables can be messy.
            text = page.extract_text()
            if not text:
                continue
                
            lines = text.split('\n')
            current_category = "General"
            current_subcategory = "General"
            
            for line in lines:
                line = line.strip()
                
                # Heuristic for category headers (often Uppercase or specific format)
                # For now, we will focus on extracting the MCCs and Descriptions
                
                match = mcc_pattern.match(line)
                if match:
                    code = match.group(1)
                    desc = match.group(2).strip()
                    
                    # Refine description (sometimes includes extra data)
                    # Also check for range
                    
                    entry = {
                        "mcc": code,
                        "description": desc,
                        "category": current_category, # Placeholder, will refine if possible
                        "subcategory": current_subcategory,
                        "range": "", # Will derive from code
                        "networks": ["V", "M"], # Default to V, M as per requirement implication, hard to parse strictly from simple text without detailed layout analysis
                        "version": "2015-07-01",
                        "active": True
                    }
                    mccs.append(entry)

    # Post-process ranges and categories if we want to be smarter
    # For 5xxx -> Retail, 6xxx -> Financial etc.
    for mcc in mccs:
        code_int = int(mcc['mcc'])
        
        # Categorize based on standard ISO 18245 ranges
        if 0 <= code_int <= 1499:
            mcc['category'] = "Agricultural Services"
        elif 1500 <= code_int <= 2999:
            mcc['category'] = "Contracted Services"
        elif 3000 <= code_int <= 3299:
            mcc['category'] = "Airlines"
        elif 3300 <= code_int <= 3499:
            mcc['category'] = "Car Rental"
        elif 3500 <= code_int <= 3999:
            mcc['category'] = "Lodging (Hotels/Motels)"
        elif 4000 <= code_int <= 4799:
            mcc['category'] = "Transportation Services"
        elif 4800 <= code_int <= 4999:
            mcc['category'] = "Utility Services"
        elif 5000 <= code_int <= 5599:
            mcc['category'] = "Retail Outlet Services"
        elif 5600 <= code_int <= 5699:
            mcc['category'] = "Clothing Stores"
        elif 5700 <= code_int <= 7299:
            mcc['category'] = "Miscellaneous Stores"
        elif 7300 <= code_int <= 7999:
            mcc['category'] = "Business Services"
        elif 8000 <= code_int <= 8999:
            mcc['category'] = "Professional Services"
        elif 9000 <= code_int <= 9999:
            mcc['category'] = "Government Services"
            
        mcc['subcategory'] = mcc['category'] # Default subcategory to category
        
        # Derive range string
        range_start = (code_int // 100) * 100
        mcc['range'] = f"{range_start}-{range_start+99}"

    # Remove duplicates
    unique_mccs = {m['mcc']: m for m in mccs}
    result = list(unique_mccs.values())
    result.sort(key=lambda x: x['mcc'])
    
    return result

def main():
    mccs = extract_mccs_from_pdf(PDF_PATH)
    print(f"Found {len(mccs)} unique MCCs.")
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(mccs, f, indent=2)
    print(f"Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
