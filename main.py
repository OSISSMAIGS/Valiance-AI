from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import json
import datetime
import threading
import time
from pymongo import MongoClient
from dotenv import load_dotenv
import mongodb_config

# Load environment variables
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Initialize the model
model = genai.GenerativeModel('gemini-2.0-flash')

# Initialize MongoDB connection using our helper
# Set a flag to track if MongoDB is enabled
mongo_enabled = False
mongo_client = None 
db = None
chat_collection = None

# Use a separate thread to initialize MongoDB to avoid blocking startup
def init_mongodb():
    global mongo_client, db, chat_collection, mongo_enabled
    try:
        mongo_client, db, chat_collection, mongo_error = mongodb_config.get_mongo_client()
        if mongo_error:
            print(f"MongoDB connection failed: {mongo_error}")
            print("App will run without MongoDB functionality")
            mongo_enabled = False
        else:
            mongo_enabled = True
            print("MongoDB connection successful")
    except Exception as e:
        print(f"Error initializing MongoDB: {str(e)}")
        mongo_enabled = False

# Start MongoDB initialization in background thread
mongodb_thread = threading.Thread(target=init_mongodb)
mongodb_thread.daemon = True  # Make thread exit when main thread exits
mongodb_thread.start()

app = Flask(__name__)

# Nama file JSON untuk menyimpan data tuning
TUNING_FILE = 'tuning_data.json'

def load_tuning_data():
    """Memuat data tuning dari file JSON, jika tidak ada file akan mengembalikan list kosong."""
    if os.path.exists(TUNING_FILE):
        with open(TUNING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_tuning_data(data):
    """Menyimpan data tuning ke file JSON."""
    with open(TUNING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Function to check MongoDB connection
def is_mongo_connected():
    if not mongo_enabled or mongo_client is None:
        return False
    try:
        # Quick check if MongoDB is still available with short timeout
        mongo_client.admin.command('ping', serverSelectionTimeoutMS=1000)
        return True
    except Exception:
        return False

# Function to save to MongoDB in a background thread
def save_to_mongodb_async(collection, data):
    def _save_task():
        try:
            start_time = time.time()
            collection.insert_one(data)
            elapsed = time.time() - start_time
            print(f"MongoDB insert completed in {elapsed:.2f} seconds")
        except Exception as e:
            print(f"MongoDB Error in background thread: {str(e)}")
    
    # Start a thread for the save operation
    thread = threading.Thread(target=_save_task)
    thread.daemon = True
    thread.start()
    return thread

# Muat data tuning saat startup
tuning_data = load_tuning_data()

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint untuk menyimpan data tuning tambahan
@app.route('/tune', methods=['POST'])
def tune():
    data = request.json
    tuning_input = data.get('input', '')
    tuning_output = data.get('output', '')
    
    if not tuning_input or not tuning_output:
        return jsonify({'response': 'Mohon berikan data tuning input dan output!'}), 400
    
    # Tambahkan data tuning baru ke list
    tuning_data.append({
        'input': tuning_input,
        'output': tuning_output
    })
    # Simpan kembali ke file JSON
    save_tuning_data(tuning_data)
    return jsonify({'response': 'Data tuning berhasil disimpan!'})

# Endpoint untuk menyimpan percakapan ke MongoDB
@app.route('/save-conversation', methods=['POST'])
def save_conversation():
    if not mongo_enabled:
        return jsonify({
            'success': False, 
            'message': 'MongoDB tidak tersedia. Percakapan tetap disimpan di localStorage.'
        }), 503
    
    data = request.json
    conversation = data.get('conversation', {})
    
    if not conversation:
        return jsonify({'success': False, 'message': 'Data percakapan kosong'}), 400
    
    # Tambahkan timestamp
    conversation['timestamp'] = datetime.datetime.now().isoformat()
    
    # Simpan ke MongoDB in background thread
    try:
        if is_mongo_connected():
            save_to_mongodb_async(chat_collection, conversation)
            return jsonify({
                'success': True,
                'message': 'Percakapan berhasil disimpan',
                'conversation_id': str(conversation.get('id', ''))
            })
        else:
            return jsonify({
                'success': False,
                'message': 'MongoDB connection lost. Percakapan tetap disimpan di localStorage.'
            }), 503
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# Endpoint untuk mengajukan pertanyaan ke AI
@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_input = data.get('message', '')
    conversation_id = data.get('conversation_id', '')
    
    if not user_input:
        return jsonify({'response': 'Mohon masukkan pesan!'})
    
    try:
        # Bangun prompt dari data tuning yang ada
        tuning_prompt = ""
        if tuning_data:
            tuning_prompt += "Berikut adalah contoh data tuning yang dapat dijadikan referensi:\n\n"
            for idx, pair in enumerate(tuning_data, start=1):
                tuning_prompt += f"Contoh {idx}:\n"
                tuning_prompt += f"Input: {pair['input']}\n"
                tuning_prompt += f"Output: {pair['output']}\n\n"
        
        # Gabungkan data tuning dengan pertanyaan pengguna dan instruksi tambahan
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
        
        # Generate respons dengan Gemini API. Parameter 'temperature' diatur melalui model_params.
        response = model.generate_content(prompt)
        ai_response = response.text
        
        # Log conversation data for analytics - MongoDB integration
        if mongo_enabled and is_mongo_connected():
            message_data = {
                'user_input': user_input,
                'ai_response': ai_response,
                'timestamp': datetime.datetime.now().isoformat(),
                'conversation_id': conversation_id
            }
            
            # Menyimpan interaksi ke MongoDB in background
            save_to_mongodb_async(chat_collection, message_data)
        
        return jsonify({'response': ai_response, 'rawMarkdown': ai_response})
    except Exception as e:
        # Jika error 429 (rate limit) terdeteksi
        if hasattr(e, 'code') and e.code == 429 or '429' in str(e):
            return jsonify({'response': 'Server sedang sibuk, silakan coba ulang lain kali (ERROR: 429)'})
        return jsonify({'response': f'Error: {str(e)}'})

# Endpoint to check MongoDB connection status - with quick timeout
@app.route('/mongodb-status')
def mongodb_status():
    status = {
        'connected': False,
        'mongodb_enabled': mongo_enabled,
        'details': {},
        'error': None
    }
    
    # Only run detailed checks if MongoDB is enabled
    if not mongo_enabled:
        status['error'] = 'MongoDB is disabled'
        return jsonify(status)
    
    try:
        if not mongo_client:
            status['error'] = 'MongoDB client was not initialized'
            return jsonify(status)
            
        # Try to ping the server with a very short timeout
        result = mongo_client.admin.command('ping', serverSelectionTimeoutMS=1000)
        status['connected'] = True
        status['details']['ping'] = result
        
        # Get database list with timeout
        status['details']['databases'] = mongo_client.list_database_names(serverSelectionTimeoutMS=1000)
        
    except Exception as e:
        status['error'] = str(e)
    
    return jsonify(status)

# Health check endpoint - for monitoring
@app.route('/health')
def health_check():
    health = {
        'status': 'ok',
        'timestamp': datetime.datetime.now().isoformat(),
        'mongo': {
            'enabled': mongo_enabled,
            'connected': False
        }
    }
    
    # Do a quick check of MongoDB if it's enabled
    if mongo_enabled:
        try:
            # Very short timeout to avoid blocking
            mongo_client.admin.command('ping', serverSelectionTimeoutMS=500)
            health['mongo']['connected'] = True
        except Exception as e:
            health['mongo']['connected'] = False
            health['mongo']['error'] = str(e)
    
    return jsonify(health)

if __name__ == '__main__':
    app.run(debug=True)
