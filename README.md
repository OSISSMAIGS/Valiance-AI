# Valiance AI Agent (Val the Phoenix)

Val the Phoenix adalah aplikasi chatbot berbasis **Flask** yang mengintegrasikan [Gemini API](https://cloud.google.com/vertex-ai/docs/generative-ai) untuk menghasilkan respons cerdas secara real-time. Aplikasi ini dirancang khusus untuk memenuhi kebutuhan OSIS SMA Ignatius Global School, menyediakan antarmuka chat yang interaktif dan mendukung _tuning_ data agar respons yang diberikan semakin akurat dan sesuai konteks.

## Daftar Isi

- [Fitur](#fitur)
- [Persyaratan](#persyaratan)
- [Instalasi dan Setup](#instalasi-dan-setup)
- [Konfigurasi](#konfigurasi)
- [Cara Menjalankan Aplikasi](#cara-menjalankan-aplikasi)
- [Endpoint API](#endpoint-api)
- [Struktur Proyek](#struktur-proyek)
- [Tuning Data dan Kustomisasi](#tuning-data-dan-kustomisasi)
- [MongoDB Chat History](#mongodb-chat-history)

## Fitur

- **Integrasi Gemini API:** Menggunakan model _Gemini-2.0 Flash_ untuk menghasilkan jawaban secara cerdas.
- **Tuning Data:** Mendukung penambahan dan pengupdate-an data tuning melalui endpoint `/tune` agar model dapat menyesuaikan respons dengan konteks website OSIS.
- **Antarmuka Chat Interaktif:** UI berbasis web dengan dukungan Markdown, syntax highlighting, dan riwayat percakapan.
- **Responsif dan User-Friendly:** Auto-resizing input, pengelolaan riwayat chat, dan fitur "New Chat" untuk memulai percakapan baru.
- **Error Handling:** Penanganan error seperti rate limit (ERROR 429) dan pengecekan validitas input.
- **Penyimpanan Riwayat Chat:** Menyimpan seluruh percakapan baik di localStorage untuk pengalaman pengguna maupun di MongoDB untuk keperluan analisis dan pengembangan.

## Persyaratan

- **Python 3.7+**
- **Flask**
- **google-generativeai**
- **python-dotenv**
- **pymongo**
- **Akun MongoDB Atlas** (untuk penyimpanan data chat)

Pastikan juga untuk memiliki kunci API yang valid untuk Gemini API dan URI koneksi untuk MongoDB.

## Instalasi dan Setup

1. **Clone repository:**

   ```bash
   git clone https://github.com/username/valiance-ai-agent.git
   cd valiance-ai-agent
   ```

2. **Buat dan aktifkan virtual environment (opsional):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/MacOS
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Konfigurasi file lingkungan:**

   Buat file `.env` di root proyek dan tambahkan variabel berikut:

   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   MONGO_URI=your_mongodb_uri_here
   ```

## Konfigurasi

- **Gemini API:** Aplikasi mengkonfigurasi Gemini API dengan membaca kunci API dari file `.env`.
- **Tuning Data:** Data tuning disimpan di file `tuning_data.json` yang berfungsi untuk menyimpan contoh-contoh pertanyaan dan respons. Data tuning ini digunakan sebagai referensi saat membangun prompt untuk Gemini API.
- **MongoDB:** Aplikasi menggunakan MongoDB untuk menyimpan riwayat percakapan. Koneksi ke MongoDB dikonfigurasi melalui variabel `MONGO_URI` di file `.env`.

## Cara Menjalankan Aplikasi

Jalankan aplikasi dengan perintah:

```bash
python app.py
```

Buka browser dan akses [http://127.0.0.1:5000](http://127.0.0.1:5000) untuk melihat antarmuka chat.

## Endpoint API

- **`/`**  
  Menampilkan halaman utama dengan antarmuka chat.

- **`/tune` (POST)**  
  Endpoint untuk menambahkan atau memperbarui data tuning.  
  **Parameter JSON:**  
  - `input`: Contoh input tuning.
  - `output`: Respons yang diharapkan dari AI.  

  **Contoh Payload:**

  ```json
  [
      {
          "input": "Bernard Febriansen",
          "output": "Hey, teman-teman VALIANCE! 😊 Yuk, kenalan sama Bernard Febriansen:\nNama: Bernard Febriansen\nNomor Jersey: 82\nSekbid: Bela Negara\nJabatan: Anggota\nKontribusinya di Bela Negara memberikan sentuhan unik pada kegiatan. Jangan lupa follow di @bernardfeb__!"
      },
  ]
  ```

  **Response:**  
  Pesan konfirmasi bahwa data tuning berhasil disimpan atau diperbarui.

- **`/ask` (POST)**  
  Endpoint untuk mengajukan pertanyaan ke AI.  
  **Parameter JSON:**  
  - `message`: Pertanyaan dari pengguna.  
  - `conversation_id`: ID unik untuk percakapan (opsional).

  **Response:**  
  - `response`: Jawaban AI dalam format Markdown.
  - `rawMarkdown`: Respons mentah sebelum di-render (jika ada).

- **`/save-conversation` (POST)**  
  Endpoint untuk menyimpan seluruh percakapan ke MongoDB.  
  **Parameter JSON:**  
  - `conversation`: Objek berisi data percakapan lengkap.

  **Response:**  
  - `success`: Status keberhasilan.
  - `message`: Pesan status.
  - `conversation_id`: ID dokumen di MongoDB (jika berhasil).

## Struktur Proyek

```
valiance-ai-agent/
├── app.py                  # File utama aplikasi Flask
├── tuning_data.json        # File untuk menyimpan dan mengupdate data tuning
├── templates/
│   ├── index.html          # Template halaman utama
│   └── layout.html         # Template layout umum
├── static/
│   ├── css/
│   │   └── style.css       # File stylesheet
│   ├── js/
│   │   ├── script.js       # Script utama UI
│   │   └── sidebar.js      # Script untuk pengelolaan sidebar
│   └── assets/
│       └── logo.png        # Logo AI
├── .env                    # File environment untuk konfigurasi API key dan MongoDB
└── .env.example            # Template file environment
```

## Tuning Data dan Kustomisasi

Data tuning adalah kunci agar AI dapat merespons dengan tepat sesuai konteks OSIS. Berikut beberapa poin penting:

- **File `tuning_data.json`:**  
  File ini berisi contoh-contoh _input_ dan _output_ yang digunakan untuk membimbing AI dalam menjawab pertanyaan. Developer dapat mengupdate file ini secara manual atau melalui endpoint `/tune`.

- **Contoh Data Tuning:**  
  Data tuning telah disediakan dengan contoh seperti:
  - **Base Prompt untuk Customer Service / AI Agent:**  
    Menginstruksikan AI untuk memberikan jawaban singkat, padat, jelas, dan menarik dengan tambahan emoji. AI hanya menjawab pertanyaan yang relevan dengan konteks website OSIS.
  - **Data Biodata Anggota OSIS:**  
    Contoh data biodata anggota seperti Bernard Febriansen, Krisensia Early Renata, Dina Evelin Cae, Richiro Huang, dan Catherine Novia Hartanto. Respons dirancang agar terdengar komunikatif, menarik, dan konsisten dengan data yang ada.

- **Penggunaan Data Tuning:**  
  Saat AI menerima pertanyaan melalui endpoint `/ask`, data tuning (jika tersedia) akan digabungkan dengan pertanyaan pengguna untuk membentuk prompt. Hal ini membantu memastikan bahwa AI:
  - Mengikuti format yang telah ditetapkan.
  - Menyertakan emoji dan gaya bahasa yang kasual serta engaging.
  - Tidak keluar dari konteks atau memberikan data yang tidak sesuai dengan dataset tuning.

## MongoDB Chat History

Aplikasi ini menyimpan riwayat percakapan di MongoDB untuk keperluan pengembangan dan analisis. Berikut detail implementasinya:

### Struktur Data

Data percakapan disimpan dalam dua bentuk:

1. **Pesan Individual** - Menyimpan setiap pasangan pesan dan respons
   - `user_input`: Pesan dari pengguna
   - `ai_response`: Respons dari AI
   - `timestamp`: Waktu pesan dikirim
   - `conversation_id`: ID unik untuk percakapan

2. **Seluruh Percakapan** - Menyimpan percakapan lengkap
   - `id`: ID unik percakapan
   - `title`: Judul percakapan (biasanya diambil dari pesan pertama)
   - `messages`: Array berisi semua pesan (user dan AI)
   - `device_info`: Informasi perangkat pengguna (browser, bahasa, dll)
   - `timestamp`: Waktu penyimpanan ke database

### Pengaksesan Data

Semua data percakapan disimpan di collection `chat_history` dalam database MongoDB. Developer dapat mengakses data ini melalui:

1. **MongoDB Atlas Dashboard**: Login ke [MongoDB Atlas](https://www.mongodb.com/cloud/atlas), pilih database `valiance_ai_db` dan collection `chat_history`
2. **MongoDB Compass**: Hubungkan dengan URI MongoDB dan jelajahi data
3. **Query API**: Gunakan pymongo atau alat lain untuk menjalankan query sesuai kebutuhan analisis

Contoh query MongoDB untuk mendapatkan percakapan terakhir:
```javascript
db.chat_history.find().sort({timestamp: -1}).limit(10)
```

### Keamanan Data

Data disimpan di MongoDB Atlas dengan keamanan standar MongoDB. Pastikan:
- URI MongoDB memiliki username/password yang aman
- Akses IP dibatasi ke alamat yang diizinkan
- Data sensitif tidak disimpan dalam plaintext

---
Copyright © 2025 Sekbid Multimedia Website Valiance