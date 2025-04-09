from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import json
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import mongodb_config
import concurrent.futures
import time

# Load environment variables
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Initialize the model
model = genai.GenerativeModel('gemini-2.0-flash')

# Initialize MongoDB connection using our helper
mongo_client, db, chat_collection, mongo_error = mongodb_config.get_mongo_client()
if mongo_error:
    print(f"MongoDB connection failed: {mongo_error}")
    print("App will run without MongoDB functionality")

app = Flask(__name__)

TUNING_FILE = 'tuning_data.json'

def load_tuning_data():
    if os.path.exists(TUNING_FILE):
        with open(TUNING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_tuning_data(data):
    with open(TUNING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def is_mongo_connected():
    if mongo_client is None:
        return False
    try:
        mongo_client.admin.command('ping')
        return True
    except:
        return False

# Load tuning data at startup
tuning_data = load_tuning_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ping')
def ping():
    return 'pong', 200

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

@app.route('/save-conversation', methods=['POST'])
def save_conversation():
    if not is_mongo_connected():
        return jsonify({
            'success': False,
            'message': 'MongoDB tidak tersedia. Percakapan tetap disimpan di localStorage.'
        }), 503

    data = request.json
    conversation = data.get('conversation', {})
    
    if not conversation:
        return jsonify({'success': False, 'message': 'Data percakapan kosong'}), 400
    
    conversation['timestamp'] = datetime.datetime.now()

    try:
        result = chat_collection.insert_one(conversation)
        return jsonify({
            'success': True,
            'message': 'Percakapan berhasil disimpan',
            'conversation_id': str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_input = data.get('message', '')
    conversation_id = data.get('conversation_id', '')

    if not user_input:
        return jsonify({'response': 'Mohon masukkan pesan!'})

    try:
        # Build prompt from tuning data
        tuning_prompt = ""
        if tuning_data:
            tuning_prompt += "Berikut adalah contoh data tuning yang dapat dijadikan referensi:\n\n"
            for idx, pair in enumerate(tuning_data, start=1):
                tuning_prompt += f"Contoh {idx}:\nInput: {pair['input']}\nOutput: {pair['output']}\n\n"

        prompt = (
            f"{tuning_prompt}"
            f"Pertanyaan: {user_input}\n\n"
            "Harap berikan respons dalam format Markdown. Gunakan sintaks Markdown seperti:\n"
            "- *teks tebal* untuk penekanan\n"
            "- teks miring untuk istilah atau frasa penting\n"
            "- # Judul, ## Sub judul, dll. untuk heading\n"
            "- - atau * untuk daftar tidak berurutan\n"
            "- 1. 2. 3. untuk daftar berurutan\n\n"
            "Penting: **Jangan sertakan label 'Input:' atau 'Output:' dalam jawaban, dan jangan ulangi pertanyaan saya. "
            "Dan jangan pernah keluar dari tuning data atau memberikan response di luar website OSIS atau biodata anggota OSIS jika diminta karena itu tidak membantu. "
            "Berikan jawaban yang bersih dan langsung."
        )

        def call_gemini(prompt_text):
            return model.generate_content(prompt_text).text

        # Start Gemini call with timeout
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(call_gemini, prompt)
            start_time = time.time()
            ai_response = future.result(timeout=20)
            duration = time.time() - start_time
            print(f"⏱ Waktu respon Gemini: {duration:.2f} detik")

        # Save to MongoDB if available
        if is_mongo_connected():
            message_data = {
                'user_input': user_input,
                'ai_response': ai_response,
                'timestamp': datetime.datetime.now(),
                'conversation_id': conversation_id
            }
            try:
                chat_collection.insert_one(message_data)
            except Exception as e:
                print(f"MongoDB Error: {str(e)}")

        return jsonify({'response': ai_response, 'rawMarkdown': ai_response})
    
    except concurrent.futures.TimeoutError:
        return jsonify({'response': 'Permintaan ke server terlalu lama. Silakan coba lagi.'}), 504
    except Exception as e:
        if hasattr(e, 'code') and e.code == 429 or '429' in str(e):
            return jsonify({'response': 'Server sedang sibuk, silakan coba ulang lain kali (ERROR: 429)'})
        return jsonify({'response': f'Error: {str(e)}'})

@app.route('/mongodb-status')
def mongodb_status():
    status = {
        'connected': False,
        'details': {},
        'error': None
    }

    connection_info = mongodb_config.get_detailed_connection_info()
    status['connection_info'] = connection_info

    try:
        if not mongo_client:
            status['error'] = 'MongoDB client was not initialized'
            return jsonify(status)

        result = mongo_client.admin.command('ping')
        status['connected'] = True
        status['details']['ping'] = result
        db_stats = {}

        for db_name in mongo_client.list_database_names():
            try:
                db = mongo_client[db_name]
                db_stats[db_name] = {'collections': db.list_collection_names()}
            except Exception as e:
                db_stats[db_name] = {'error': str(e)}

        status['details']['db_stats'] = db_stats
    except Exception as e:
        status['error'] = str(e)

    return jsonify(status)

if __name__ == '__main__':
    app.run(debug=True)
