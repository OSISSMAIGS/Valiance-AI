from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import traceback

# Load environment variables
load_dotenv()

# Configure MongoDB
MONGODB_URI = os.getenv('MONGO_URI')
mongo_client = None
db = None
conversations_collection = None
mongodb_connected = False
tz_jakarta = timezone(timedelta(hours=7))

# Try to connect to MongoDB, but continue if it fails
try:
    if MONGODB_URI:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)  # 5 second timeout
        # Test the connection
        mongo_client.server_info()
        db = mongo_client['valiance_ai_db']  # Use the correct database name
        conversations_collection = db['conversations']
        mongodb_connected = True
        print("MongoDB connected successfully")
except Exception as e:
    print(f"MongoDB connection failed: {str(e)}")
    mongo_client = None
    db = None
    conversations_collection = None
    mongodb_connected = False

# Configure the Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Initialize the model
model = genai.GenerativeModel('gemini-2.0-flash')

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

# Endpoint untuk mengajukan pertanyaan ke AI
@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_input = data.get('message', '')
    
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
        
        return jsonify({'response': ai_response, 'rawMarkdown': ai_response})
    except Exception as e:
        # Jika error 429 (rate limit) terdeteksi
        if hasattr(e, 'code') and e.code == 429 or '429' in str(e):
            return jsonify({'response': 'Server sedang sibuk, silakan coba ulang lain kali (ERROR: 429)'})
        return jsonify({'response': f'Error: {str(e)}'})

@app.route('/sync-conversations', methods=['POST'])
def sync_conversations():
    # Check if MongoDB is connected
    if not mongodb_connected:
        return jsonify({'status': 'warning', 'message': 'MongoDB is not connected, data saved locally only'})
    
    try:
        data = request.json
        conversations = data.get('conversations', [])
        user_id = data.get('user_id', 'anonymous')
        
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
        print(f"Error syncing conversations: {str(e)}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get-conversations', methods=['GET'])
def get_conversations():
    # This endpoint is now disabled for security reasons
    return jsonify({'status': 'error', 'message': 'Access denied', 'conversations': []}), 403

if __name__ == '__main__':
    app.run(debug=True)
