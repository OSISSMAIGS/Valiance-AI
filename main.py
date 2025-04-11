# Tambahkan di paling atas
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import traceback
import bcrypt
from functools import wraps

# Load environment variables
load_dotenv()

# Configure MongoDB
MONGODB_URI = os.getenv('MONGO_URI')
mongo_client = None
db = None
conversations_collection = None
admin_users_collection = None
mongodb_connected = False
tz_jakarta = timezone(timedelta(hours=7))

try:
    if MONGODB_URI:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        mongo_client.server_info()
        db = mongo_client['valiance_ai_db']
        conversations_collection = db['conversations']
        admin_users_collection = db['admin_users']
        mongodb_connected = True
        print("MongoDB connected successfully")
except Exception as e:
    print(f"MongoDB connection failed: {str(e)}")
    mongo_client = None
    db = None
    conversations_collection = None
    admin_users_collection = None
    mongodb_connected = False

# Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Inisialisasi Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'valiance_default_secret_key')
app.permanent_session_lifetime = timedelta(hours=24)

# Tuning data
TUNING_FILE = 'tuning_data.json'

def load_tuning_data():
    if os.path.exists(TUNING_FILE):
        with open(TUNING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_tuning_data(data):
    with open(TUNING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

tuning_data = load_tuning_data()

# Admin login decorator
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
    data = request.json
    tuning_input = data.get('input', '')
    tuning_output = data.get('output', '')
    
    if not tuning_input or not tuning_output:
        return jsonify({'response': 'Mohon berikan data tuning input dan output!'}), 400
    
    tuning_data.append({
        'input': tuning_input,
        'output': tuning_output
    })
    save_tuning_data(tuning_data)
    return jsonify({'response': 'Data tuning berhasil disimpan!'})

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return jsonify({'response': 'Mohon masukkan pesan!'})
    
    try:
        tuning_prompt = ""
        if tuning_data:
            tuning_prompt += "Berikut adalah contoh data tuning yang dapat dijadikan referensi:\n\n"
            for idx, pair in enumerate(tuning_data, start=1):
                tuning_prompt += f"Contoh {idx}:\n"
                tuning_prompt += f"Input: {pair['input']}\n"
                tuning_prompt += f"Output: {pair['output']}\n\n"
        
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

        # Inisialisasi model DI SINI SAJA (tidak di global)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        ai_response = response.text
        
        return jsonify({'response': ai_response, 'rawMarkdown': ai_response})
    except Exception as e:
        if hasattr(e, 'code') and e.code == 429 or '429' in str(e):
            return jsonify({'response': 'Server sedang sibuk, silakan coba ulang lain kali (ERROR: 429)'})
        return jsonify({'response': f'Error: {str(e)}'})

@app.route('/sync-conversations', methods=['POST'])
def sync_conversations():
    if not mongodb_connected:
        return jsonify({'status': 'warning', 'message': 'MongoDB is not connected, data saved locally only'})
    
    try:
        data = request.json
        conversations = data.get('conversations', [])
        user_id = data.get('user_id', 'anonymous')
        
        for conv in conversations:
            conv['last_synced'] = datetime.now(tz_jakarta)
            conv['user_id'] = user_id
            
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
        print(f"Error syncing conversations: {str(e)}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get-conversations', methods=['GET'])
def get_conversations():
    return jsonify({'status': 'error', 'message': 'Access denied', 'conversations': []}), 403

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not mongodb_connected:
            error = "Database tidak tersedia. Silakan coba lagi nanti."
        else:
            admin_user = admin_users_collection.find_one({'username': username})
            if admin_user and bcrypt.checkpw(password.encode('utf-8'), admin_user['password']):
                session.permanent = True
                session['admin_logged_in'] = True
                session['admin_username'] = username
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
    if not mongodb_connected:
        return render_template('admin/dashboard.html', error="Database tidak tersedia", conversations=[], unique_users_count=0)
    
    try:
        conversations_cursor = conversations_collection.find().sort('last_synced', -1)
        conversations = list(conversations_cursor)
        
        unique_users = set()
        for conv in conversations:
            if 'user_id' in conv:
                unique_users.add(conv['user_id'])
        unique_users_count = len(unique_users)
        
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
        print(f"Error loading admin dashboard: {str(e)}")
        traceback.print_exc()
        return render_template('admin/dashboard.html', error=str(e), conversations=[], unique_users_count=0)

@app.route('/setup-admin', methods=['POST'])
def setup_admin():
    if not mongodb_connected:
        return jsonify({'status': 'error', 'message': 'MongoDB is not connected'}), 500
    
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        secret_key = data.get('secret_key')
        
        admin_setup_key = os.getenv('ADMIN_SETUP_KEY')
        if not admin_setup_key or secret_key != admin_setup_key:
            return jsonify({'status': 'error', 'message': 'Invalid secret key'}), 403
        
        existing_admin = admin_users_collection.find_one({'username': username})
        if existing_admin:
            return jsonify({'status': 'error', 'message': 'Admin user already exists'}), 400
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        admin_users_collection.insert_one({
            'username': username,
            'password': hashed_password,
            'created_at': datetime.now(tz_jakarta)
        })
        
        return jsonify({'status': 'success', 'message': 'Admin user created successfully'})
    except Exception as e:
        print(f"Error setting up admin: {str(e)}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

# === DI SINI YANG DIUBAH ===
if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)
