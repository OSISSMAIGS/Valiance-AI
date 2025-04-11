import os
import sys
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import google.generativeai as genai
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import traceback
import bcrypt
from functools import wraps
import gc
import signal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('app')

# Register signal handlers to log termination signals
def signal_handler(sig, frame):
    logger.warning(f"Received signal {sig}, terminating application...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)  # SIGTERM (signal 15)
signal.signal(signal.SIGINT, signal_handler)   # SIGINT (Ctrl+C)

# Load environment variables
load_dotenv()

# Tuning data file
TUNING_FILE = 'tuning_data.json'

# Configure MongoDB
MONGODB_URI = os.getenv('MONGO_URI')
mongo_client = None
db = None
conversations_collection = None
admin_users_collection = None
mongodb_connected = False
tz_jakarta = timezone(timedelta(hours=7))

# Try to connect to MongoDB, but continue if it fails
try:
    if MONGODB_URI:
        mongo_client = MongoClient(
            MONGODB_URI, 
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            maxPoolSize=10,  # Limit connection pool size
            maxIdleTimeMS=30000  # Close idle connections after 30 seconds
        )
        # Test the connection
        mongo_client.server_info()
        db = mongo_client['valiance_ai_db']
        conversations_collection = db['conversations']
        admin_users_collection = db['admin_users']
        mongodb_connected = True
        logger.info("MongoDB connected successfully")
except Exception as e:
    logger.error(f"MongoDB connection failed: {str(e)}")
    mongo_client = None
    db = None
    conversations_collection = None
    admin_users_collection = None
    mongodb_connected = False

# Configure the Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Initialize the model (avoid creating this inside route handlers)
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
    logger.info("Gemini model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini model: {str(e)}")
    model = None

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'valiance_default_secret_key')
app.permanent_session_lifetime = timedelta(hours=24)

# Load tuning data with memory optimization
def load_tuning_data():
    """Load tuning data from file with memory optimization."""
    try:
        if os.path.exists(TUNING_FILE):
            file_size = os.path.getsize(TUNING_FILE) / (1024 * 1024)  # Size in MB
            logger.info(f"Loading tuning data file ({file_size:.2f} MB)")
            
            if file_size > 50:  # If file is larger than 50MB
                logger.warning(f"Tuning data file is large ({file_size:.2f} MB), this might cause memory issues")
                
            with open(TUNING_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data)} tuning examples")
            return data
        else:
            logger.warning(f"Tuning data file {TUNING_FILE} not found")
            return []
    except Exception as e:
        logger.error(f"Error loading tuning data: {str(e)}")
        return []

# Use a global variable for tuning data to avoid reloading for each request
tuning_data = load_tuning_data()

# Login decorator for admin routes
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tune', methods=['POST'])
def tune():
    global tuning_data
    
    try:
        data = request.json
        tuning_input = data.get('input', '')
        tuning_output = data.get('output', '')
        
        if not tuning_input or not tuning_output:
            return jsonify({'response': 'Mohon berikan data tuning input dan output!'}), 400
        
        # Add new tuning data
        tuning_data.append({
            'input': tuning_input,
            'output': tuning_output
        })
        
        # Save to file
        try:
            with open(TUNING_FILE, 'w', encoding='utf-8') as f:
                json.dump(tuning_data, f, ensure_ascii=False, indent=4)
            logger.info(f"Tuning data saved, now contains {len(tuning_data)} examples")
        except Exception as e:
            logger.error(f"Error saving tuning data: {str(e)}")
            return jsonify({'response': f'Error saving tuning data: {str(e)}'}), 500
        
        return jsonify({'response': 'Data tuning berhasil disimpan!'})
    except Exception as e:
        logger.error(f"Error in /tune endpoint: {str(e)}")
        return jsonify({'response': f'Error: {str(e)}'}), 500

@app.route('/ask', methods=['POST'])
def ask():
    if model is None:
        return jsonify({'response': 'AI model is not available. Please try again later.'}), 503
    
    try:
        data = request.json
        user_input = data.get('message', '')
        
        if not user_input:
            return jsonify({'response': 'Mohon masukkan pesan!'})
        
        # Build prompt with limited examples to save memory
        tuning_prompt = ""
        if tuning_data:
            # Limit to max 10 examples to avoid excessive memory usage
            examples_to_use = tuning_data[:10] if len(tuning_data) > 10 else tuning_data
            tuning_prompt += "Berikut adalah contoh data tuning yang dapat dijadikan referensi:\n\n"
            for idx, pair in enumerate(examples_to_use, start=1):
                tuning_prompt += f"Contoh {idx}:\n"
                tuning_prompt += f"Input: {pair['input']}\n"
                tuning_prompt += f"Output: {pair['output']}\n\n"
        
        # Combined prompt
        prompt = (
            f"{tuning_prompt}"
            f"Pertanyaan: {user_input}\n\n"
            "Harap berikan respons dalam format Markdown. Gunakan sintaks Markdown seperti:\n"
            "- *teks tebal* untuk penekanan\n"
            "- teks miring untuk istilah atau frasa penting\n"
            "- # Judul, ## Sub judul, dll. untuk heading\n"
            "- - atau * untuk daftar tidak berurutan\n"
            "- 1. 2. 3. untuk daftar berurutan\n\n"
            "Penting: **Jangan sertakan label 'Input:' atau 'Output:' dalam jawaban, dan jangan ulangi pertanyaan saya. dan jangan pernah keluar dari tuning data atau memberikan rensponse diluar website OSIS atau biodata anggota OSIS jika diminta karena itu akan sangat tidak membantu "
            "Berikan jawaban yang bersih dan langsung."
        )
        
        # Generate response with Gemini API
        try:
            response = model.generate_content(prompt)
            ai_response = response.text
            
            # Force garbage collection to free memory
            gc.collect()
            
            return jsonify({'response': ai_response, 'rawMarkdown': ai_response})
        except Exception as e:
            # Handle API errors
            error_message = str(e)
            if '429' in error_message:
                logger.warning("Rate limit error from Gemini API")
                return jsonify({'response': 'Server sedang sibuk, silakan coba ulang lain kali (ERROR: 429)'})
            else:
                logger.error(f"Gemini API error: {error_message}")
                return jsonify({'response': f'Error saat mengakses AI: {error_message}'})
    except Exception as e:
        logger.error(f"Error in /ask endpoint: {str(e)}")
        return jsonify({'response': f'Error: {str(e)}'}), 500

@app.route('/sync-conversations', methods=['POST'])
def sync_conversations():
    # Check if MongoDB is connected
    if not mongodb_connected:
        return jsonify({'status': 'warning', 'message': 'MongoDB is not connected, data saved locally only'})
    
    try:
        data = request.json
        conversations = data.get('conversations', [])
        user_id = data.get('user_id', 'anonymous')
        
        # Limit the number of conversations to process at once
        max_conversations = 10
        if len(conversations) > max_conversations:
            logger.warning(f"Limiting sync to {max_conversations} conversations (received {len(conversations)})")
            conversations = conversations[:max_conversations]
        
        # Update or insert conversations
        for conv in conversations:
            # Convert datetime strings for compatibility
            conv['last_synced'] = datetime.now(tz_jakarta)
            conv['user_id'] = user_id
            
            # Handle serializable date fields if any
            if 'created_at' in conv and isinstance(conv['created_at'], str):
                try:
                    conv['created_at'] = datetime.fromisoformat(conv['created_at'].replace('Z', '+00:00'))
                except:
                    pass
            
            conversations_collection.update_one(
                {'id': conv['id']},
                {'$set': conv},
                upsert=True
            )
        
        return jsonify({'status': 'success', 'message': 'Conversations synced successfully'})
    except Exception as e:
        logger.error(f"Error syncing conversations: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if MongoDB is connected
        if not mongodb_connected:
            error = "Database tidak tersedia. Silakan coba lagi nanti."
        else:
            # Find the admin user
            admin_user = admin_users_collection.find_one({'username': username})
            
            # Check if admin user exists and password is correct
            if admin_user and bcrypt.checkpw(password.encode('utf-8'), admin_user['password']):
                # Create session
                session.permanent = True
                session['admin_logged_in'] = True
                session['admin_username'] = username
                
                # Redirect to dashboard
                return redirect(url_for('admin_dashboard'))
            else:
                error = "Username atau password salah."
    
    return render_template('admin/login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_login_required
def admin_dashboard():
    # Check if MongoDB is connected
    if not mongodb_connected:
        return render_template('admin/dashboard.html', error="Database tidak tersedia", conversations=[], unique_users_count=0)
    
    try:
        # Limit the number of conversations to display
        limit = 100
        # Get conversations from MongoDB with limit
        conversations_cursor = conversations_collection.find().sort('last_synced', -1).limit(limit)
        conversations = list(conversations_cursor)
        
        # Calculate unique users count
        unique_users = set()
        for conv in conversations:
            if 'user_id' in conv:
                unique_users.add(conv['user_id'])
        unique_users_count = len(unique_users)
        
        # Format dates for display
        for conv in conversations:
            if 'last_synced' in conv:
                if isinstance(conv['last_synced'], datetime):
                    conv['last_synced_formatted'] = conv['last_synced'].strftime('%d-%m-%Y %H:%M:%S')
                else:
                    conv['last_synced_formatted'] = 'N/A'
            else:
                conv['last_synced_formatted'] = 'N/A'
        
        return render_template('admin/dashboard.html', conversations=conversations, unique_users_count=unique_users_count)
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}", exc_info=True)
        return render_template('admin/dashboard.html', error=str(e), conversations=[], unique_users_count=0)

# The application object for WSGI servers
application = app

if __name__ == '__main__':
    app.run(debug=False, threaded=True) 