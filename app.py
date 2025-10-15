# app.py
from flask import Flask, render_template, request, jsonify, send_from_directory
from docling.document_converter import DocumentConverter
import re
import os
import tempfile

app = Flask(__name__)

# Serve service worker with correct MIME type
@app.route('/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

# Serve manifest.json
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

def is_hk_electric_bill(text):
    """Check if the document is a HK Electric bill"""
    return "The Hongkong Electric Co., Ltd." in text and "HK Electric" in text

def extract_bill_info(text):
    """Extract specific information from HK Electric bill"""
    info = {
        'recipient_name': '',
        'recipient_address': '',
        'account_number': '',
        'date_of_bill': '',
        'amount_due': '',
        'is_electric_bill': False
    }
    
    # Check if this is an HK Electric bill
    if not is_hk_electric_bill(text):
        return info
    
    info['is_electric_bill'] = True
    
    # Extract recipient name (under company name)
    name_pattern = r'The Hongkong Electric Co\., Ltd\.\s*\n([A-Z][A-Z\s]+)\n'
    name_match = re.search(name_pattern, text)
    if name_match:
        info['recipient_name'] = name_match.group(1).strip()
    
    # Extract recipient address (multi-line after name)
    address_section = re.search(r'The Hongkong Electric Co\., Ltd\.\s*\n[A-Z\s]+\n((?:.+\n)+?)(?=Residential|Account|Deposit|$)', text)
    if address_section:
        address_lines = address_section.group(1).strip().split('\n')
        cleaned_address = []
        for line in address_lines:
            line = line.strip()
            if line and not any(keyword in line for keyword in ['Residential', 'Tariff', 'Deposit', 'Account']):
                cleaned_address.append(line)
        if cleaned_address:
            info['recipient_address'] = ', '.join(cleaned_address)
    
    # Extract account number
    account_pattern = r'Account Number\s*([0-9]{10})'
    account_match = re.search(account_pattern, text)
    if account_match:
        info['account_number'] = account_match.group(1).strip()
    
    # Extract date of bill
    date_pattern = r'Date of Bill\s*([0-9]{2}/[0-9]{2}/[0-9]{4})'
    date_match = re.search(date_pattern, text)
    if date_match:
        info['date_of_bill'] = date_match.group(1).strip()
    
    # Extract amount due
    amount_patterns = [
        r'Please Pay This Amount\s*\$?\s*([0-9,]+\.?[0-9]*)',
        r'Total Amount Due\s*\$?\s*([0-9,]+\.?[0-9]*)',
        r'Amount Due\s*\$?\s*([0-9,]+\.?[0-9]*)'
    ]
    
    for pattern in amount_patterns:
        amount_matches = re.findall(pattern, text)
        if amount_matches:
            amount = amount_matches[-1].replace(',', '')
            info['amount_due'] = amount
            break
    
    return info

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan_document():
    """Endpoint to scan and process uploaded document"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpeg') as temp_file:
        file.save(temp_file.name)
        temp_file_path = temp_file.name
    
    try:
        # Convert the saved file using DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(temp_file_path)
        extracted_text = result.document.export_to_markdown()
        
        # Extract bill information
        bill_info = extract_bill_info(extracted_text)
        
        return jsonify(bill_info)
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass

@app.route('/process_url', methods=['POST'])
def process_url():
    """Endpoint to process document from URL"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
        
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        # Convert URL to document
        converter = DocumentConverter()
        result = converter.convert(url)
        extracted_text = result.document.export_to_markdown()
        
        # Extract bill information
        bill_info = extract_bill_info(extracted_text)
        
        return jsonify(bill_info)
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/test_sample')
def test_sample():
    """Test endpoint using the sample address.jpeg"""
    try:
        # Use the sample image path
        sample_path = "address.jpeg"
        
        if not os.path.exists(sample_path):
            return jsonify({'error': 'Sample file not found'}), 404
            
        converter = DocumentConverter()
        result = converter.convert(sample_path)
        extracted_text = result.document.export_to_markdown()
        
        # Extract bill information
        bill_info = extract_bill_info(extracted_text)
        
        return jsonify(bill_info)
        
    except Exception as e:
        return jsonify({'error': f'Test failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("Starting development server on http://localhost:5000")
    print("For mobile testing, use the IP address of your computer")
    app.run(host="0.0.0.0", port='5000', debug=True)
