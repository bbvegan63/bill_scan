from flask import Flask, render_template, request, jsonify, send_from_directory
from flask import session, redirect, url_for, flash # NEW: for session/login management
from docling.document_converter import DocumentConverter
import re
import os
import tempfile
from supabase import create_client, Client
import uuid
from datetime import datetime, timedelta # NEW: for session lifetime
import json
import mimetypes # NEW: for content-type
from werkzeug.utils import secure_filename # NEW: for securing filenames
from dotenv import load_dotenv # NEW: for loading .env file

# Load environment variables from .env file (if you have one)
load_dotenv() 

app = Flask(__name__)

# IMPORTANT: Set a secret key for message flashing and session management
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60) # Set session timeout

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://ucpflprqqcbukidbrlnn.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'your-supabase-anon-key-here')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')  # Service role key for bypassing RLS
BUCKET_NAME = "documents" # NEW: Define the bucket name for file uploads

# Allowed file extensions for security (for file upload)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    """Checks if a file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize Supabase clients
try:
    # Regular client for public/authenticated operations
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Service role client for database operations (bypasses RLS)
    if SUPABASE_SERVICE_KEY:
        supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    else:
        supabase_admin = supabase
        print("Service role key not provided, using regular client (RLS may block operations)")
        
except Exception as e:
    print(f"Supabase client initialization warning: {e}")
    supabase = None
    supabase_admin = None

# --- AUTHENTICATION ROUTES (MODIFIED login function) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            session_data = response.session 

            if session_data and session_data.access_token and session_data.refresh_token:
                # Store BOTH tokens AND THE USER ID in the Flask session
                session['supabase_session'] = {
                    'access_token': session_data.access_token,
                    'refresh_token': session_data.refresh_token,
                    'user_id': session_data.user.id # <--- THIS IS THE CRITICAL ADDITION
                }
                flash('Login successful!', 'success')
                return redirect(url_for('index')) # Redirect to the index page
            else:
                flash('Login failed: Invalid credentials or session error.', 'error')
                
        except Exception as e:
            flash(f'An authentication error occurred: {e}', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('supabase_session', None) # Clear the session key
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

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
    
    info['is_electric_bill'] = is_hk_electric_bill(text)
    
    # Placeholder for extraction logic
    if info['is_electric_bill']:    
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

def save_to_document_table(original_filename, extracted_data, file_url=None, user_id=None, document_type=None, property_id=None, tenant_id=None, lease_id=None):
    """Save document information to the document table using the standard client (MUST be authenticated for RLS)"""
    if not supabase: # Use the STANDARD client
        print("Supabase standard client not available, skipping database insert")
        return None
    
    # CRITICAL: We MUST ensure user_id is set here to match the RLS policy (auth.uid())
    if not user_id:
        print("Error: User ID is required for RLS-compliant insert.")
        return None
    
    try:
        # Prepare document data
        document_data = {
            'document_type': document_type or 'utility_bill',
            'title': original_filename,
            'file_urls': [file_url] if file_url else [],
            'upload_date': datetime.now().isoformat(),
            'extracted_data': json.dumps(extracted_data),
            'property_id': property_id,
            'tenant_id': tenant_id,
            'lease_id': lease_id,
            'user_id': user_id # Passed from the session in scan_document
        }
        
        # Remove None values
        document_data = {k: v for k, v in document_data.items() if v is not None}
        
        # Insert into document table using the STANDARD client (will be RLS-checked)
        insert_result = supabase.table('document').insert(document_data).execute()
        
        if hasattr(insert_result, 'error') and insert_result.error:
             # PostgREST/RLS error is often in result.error
            print(f"Database insert error: {insert_result.error}")
            return None
        
        print(f"Document record created with ID: {insert_result.data[0]['id'] if insert_result.data else 'unknown'}")
        return insert_result.data[0]['id'] if insert_result.data else None
        
    except APIError as e: # Catch PostgREST API/RLS errors explicitly
        print(f"RLS/API Error during database insert: {e.message}")
        return None
    except Exception as e:
        print(f"Error saving to document table: {e}")
        return None

def setup_rls_policies():
    """Setup Row Level Security policies for the document table to use auth.uid()"""
    if not supabase_admin or not SUPABASE_SERVICE_KEY:
        print("Cannot setup RLS policies: Admin client not available (Service Role Key missing)")
        return False
    
    try:
        # SQL to create RLS policies for a standard multi-tenant app
        policies_sql = """
        -- Enable RLS
        ALTER TABLE document ENABLE ROW LEVEL SECURITY;

        -- Policy for authenticated insert (Allow insert only if user_id matches auth.uid())
        DROP POLICY IF EXISTS "Authenticated users can insert their documents" ON document;
        CREATE POLICY "Authenticated users can insert their documents" ON document
        FOR INSERT 
        WITH CHECK (auth.uid() = user_id);

        -- Policy for authenticated select (Allow select only if user_id matches auth.uid())
        DROP POLICY IF EXISTS "Authenticated users can view their documents" ON document;
        CREATE POLICY "Authenticated users can view their documents" ON document
        FOR SELECT 
        USING (auth.uid() = user_id);

        -- Optional: Policies for update/delete would follow the same pattern
        """
        
        # Execute the SQL using the ADMIN client
        result = supabase_admin.rpc('exec_sql', {'sql': policies_sql}).execute()
        print("RLS policies setup completed (INSERT/SELECT limited to auth.uid())")
        return True
        
    except Exception as e:
        print(f"Error setting up RLS policies: {e}")
        return False

@app.route('/')
def index():
    # NEW: Pass session status to template for UI display
    is_logged_in = 'supabase_session' in session
    return render_template('index.html', is_logged_in=is_logged_in)

@app.route('/scan', methods=['POST'])
def scan_document():
    """Endpoint to scan and process uploaded document, NOW including storage upload"""
    
    # --- AUTHENTICATION CHECK ---
    if 'supabase_session' not in session:
        return jsonify({'error': 'Authentication required. Please log in first.'}), 401
    
    # Get tokens
    session_data = session['supabase_session']
    access_token = session_data['access_token']
    refresh_token = session_data['refresh_token']
    user_id_from_session = session_data['user_id'] # NEW: Retrieve user ID
    
    # Set the authenticated session on the global client for the request
    try:
        supabase.auth.set_session(access_token, refresh_token) 
    except Exception as e:
        # Token is likely expired. Clear session and force re-login.
        session.pop('supabase_session', None)
        return jsonify({'error': f'Session Expired or Error: {str(e)}. Please log in again.'}), 401
    
    # --- FILE HANDLING ---
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    original_filename = secure_filename(file.filename)
    if not allowed_file(original_filename):
        return jsonify({'error': 'File type not allowed.'}), 400
    
    document_type = request.form.get('document_type', 'utility_bill')
    property_id = request.form.get('property_id')
    tenant_id = request.form.get('tenant_id')
    lease_id = request.form.get('lease_id')
    
    # Convert numeric IDs to integers if provided
    if property_id:
        try:
            property_id = int(property_id)
        except ValueError:
            property_id = None
    
    if tenant_id:
        try:
            tenant_id = int(tenant_id)
        except ValueError:
            tenant_id = None
    
    if lease_id:
        try:
            lease_id = int(lease_id)
        except ValueError:
            lease_id = None
    
    temp_file_path = None
    uploaded_file_url = None
    
    try:
        # Read file content for both OCR (via temp file) and Supabase upload
        file_content = file.read()
        file_mime_type, _ = mimetypes.guess_type(original_filename)
        if not file_mime_type:
            file_mime_type = 'application/octet-stream'

        # --- 1. SAVE TO TEMPORARY FILE FOR OCR ---
        # Create temporary file (use original extension for DocumentConverter)
        _, ext = os.path.splitext(original_filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        # --- 2. PERFORM OCR ---
        converter = DocumentConverter()
        result = converter.convert(temp_file_path)
        extracted_text = result.document.export_to_markdown()
        bill_info = extract_bill_info(extracted_text)

        # --- 3. UPLOAD TO SUPABASE STORAGE ---
        # Use user's ID or UUID + original name for path
        unique_filename = f"{uuid.uuid4()}-{original_filename}"
        storage_path = f"{user_id_from_session}/{unique_filename}"

        # The upload_response variable now receives a non-dict object (UploadResponse) on success.
        # We skip the manual dict check as the SDK will raise an exception on failure.
        supabase.storage.from_(BUCKET_NAME).upload(
            file=file_content, # Upload the content read earlier
            path=storage_path, 
            file_options={"content-type": file_mime_type}
        )

        # The manual error check is removed to resolve the "not iterable" error.
        # We proceed, assuming the upload was successful since no exception was raised.

        # Get the public URL for the saved file (if the bucket is public)
        uploaded_file_url = supabase.storage.from_(BUCKET_NAME).get_public_url(storage_path)
        bill_info['uploaded_file_url'] = uploaded_file_url
        bill_info['upload_success'] = True
        
        # --- 4. SAVE METADATA TO DATABASE ---
        document_id = save_to_document_table(
            original_filename=original_filename,
            extracted_data=bill_info,
            file_url=uploaded_file_url, # Pass the URL to be saved
            user_id=user_id_from_session,
            document_type=document_type,
            property_id=property_id,
            tenant_id=tenant_id,
            lease_id=lease_id
        )
        
        if document_id:
            bill_info['document_id'] = document_id
            bill_info['database_save_success'] = True
        else:
            bill_info['document_id'] = None
            bill_info['database_save_success'] = False
        
        return jsonify(bill_info)
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500
    finally:
        # Clean up temporary file
        if temp_file_path:
            try:
                os.unlink(temp_file_path)
            except:
                pass

@app.route('/process_url', methods=['POST'])
def process_url():
    """Endpoint to process document from URL - only save to database"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
        
    url = data.get('url')
    user_id = data.get('user_id')
    document_type = data.get('document_type', 'utility_bill')
    property_id = data.get('property_id')
    tenant_id = data.get('tenant_id')
    lease_id = data.get('lease_id')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        # Convert URL to document
        converter = DocumentConverter()
        result = converter.convert(url)
        extracted_text = result.document.export_to_markdown()
        
        # Extract bill information
        bill_info = extract_bill_info(extracted_text)
        
        # For URL processing, store the original URL in file_urls
        bill_info['original_url'] = url
        
        # Save to document table with extracted data
        document_id = save_to_document_table(
            original_filename=url.split('/')[-1] if '/' in url else url,
            extracted_data=bill_info,
            user_id=user_id,
            document_type=document_type,
            property_id=property_id,
            tenant_id=tenant_id,
            lease_id=lease_id
        )
        
        if document_id:
            bill_info['document_id'] = document_id
            bill_info['database_save_success'] = True
        else:
            bill_info['document_id'] = None
            bill_info['database_save_success'] = False
        
        # Set upload fields
        bill_info['upload_success'] = True  # URL processing is considered successful
        
        return jsonify(bill_info)
        
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/test_sample')
def test_sample():
    """Test endpoint using the sample address.jpeg - only save to database"""
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
        
        # Save to document table (skip storage upload)
        document_id = save_to_document_table(
            original_filename="sample_address.jpeg",
            extracted_data=bill_info,
            document_type='test_utility_bill'
        )
        
        if document_id:
            bill_info['document_id'] = document_id
            bill_info['database_save_success'] = True
        else:
            bill_info['document_id'] = None
            bill_info['database_save_success'] = False
        
        # Set upload fields
        bill_info['uploaded_file_url'] = None
        bill_info['upload_success'] = False
        
        return jsonify(bill_info)
        
    except Exception as e:
        return jsonify({'error': f'Test failed: {str(e)}'}), 500

@app.route('/setup_rls', methods=['POST'])
def setup_rls_endpoint():
    """Endpoint to setup RLS policies (run this once)"""
    try:
        success = setup_rls_policies()
        if success:
            return jsonify({'message': 'RLS policies setup successfully'})
        else:
            return jsonify({'error': 'Failed to setup RLS policies'}), 500
    except Exception as e:
        return jsonify({'error': f'RLS setup failed: {str(e)}'}), 500

@app.route('/documents', methods=['GET'])
def get_documents():
    """Endpoint to retrieve documents from the database"""
    if not supabase:
        return jsonify({'error': 'Supabase client not available'}), 500
        
    try:
        user_id = request.args.get('user_id')
        property_id = request.args.get('property_id')
        tenant_id = request.args.get('tenant_id')
        document_type = request.args.get('document_type')
        
        # Use admin client to bypass RLS for reading
        query = supabase_admin.table('document').select('*')
        
        if user_id:
            query = query.eq('user_id', user_id)
        if property_id:
            query = query.eq('property_id', property_id)
        if tenant_id:
            query = query.eq('tenant_id', tenant_id)
        if document_type:
            query = query.eq('document_type', document_type)
        
        result = query.execute()
        
        if hasattr(result, 'error') and result.error:
            return jsonify({'error': f'Database query failed: {result.error}'}), 500
        
        # Parse extracted_data from JSON string back to object for response
        documents = result.data
        for doc in documents:
            if doc.get('extracted_data'):
                try:
                    doc['extracted_data'] = json.loads(doc['extracted_data'])
                except:
                    # If parsing fails, keep as string
                    pass
        
        return jsonify({'documents': documents})
        
    except Exception as e:
        return jsonify({'error': f'Query failed: {str(e)}'}), 500

@app.route('/documents/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """Endpoint to retrieve a specific document by ID"""
    if not supabase:
        return jsonify({'error': 'Supabase client not available'}), 500
        
    try:
        result = supabase_admin.table('document').select('*').eq('id', document_id).execute()
        
        if hasattr(result, 'error') and result.error:
            return jsonify({'error': f'Database query failed: {result.error}'}), 500
        
        if not result.data:
            return jsonify({'error': 'Document not found'}), 404
        
        document = result.data[0]
        
        # Parse extracted_data from JSON string back to object
        if document.get('extracted_data'):
            try:
                document['extracted_data'] = json.loads(document['extracted_data'])
            except:
                # If parsing fails, keep as string
                pass
        
        return jsonify({'document': document})
        
    except Exception as e:
        return jsonify({'error': f'Query failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("Starting development server on http://localhost:5000")
    print("For mobile testing, use the IP address of your computer")
    print("Note: Files will be processed and saved to database only (no storage upload)")
    
    # Try to setup RLS policies on startup
    if supabase_admin:
        print("Attempting to setup RLS policies...")
        setup_rls_policies()
    
    app.run(host="0.0.0.0", port='5000', debug=True)
