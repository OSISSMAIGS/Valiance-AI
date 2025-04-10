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
- [Keamanan Data](#keamanan-data)

## Fitur

- **Integrasi Gemini API:** Menggunakan model _Gemini-2.0 Flash_ untuk menghasilkan jawaban secara cerdas.
- **Tuning Data:** Mendukung penambahan dan pengupdate-an data tuning melalui endpoint `/tune` agar model dapat menyesuaikan respons dengan konteks website OSIS.
- **Antarmuka Chat Interaktif:** UI berbasis web dengan dukungan Markdown, syntax highlighting, dan riwayat percakapan.
- **Responsif dan User-Friendly:** Auto-resizing input, pengelolaan riwayat chat, dan fitur "New Chat" untuk memulai percakapan baru.
- **Error Handling:** Penanganan error seperti rate limit (ERROR 429) dan pengecekan validitas input.
- **Penyimpanan Riwayat Chat:** Menyimpan seluruh percakapan di localStorage untuk pengalaman pengguna dan secara aman di-backup ke MongoDB (one-way sync).
- **Keamanan Data:** Isolasi data pengguna dengan sistem sinkronisasi satu arah dari local storage ke MongoDB.
- **Fault Tolerance:** Aplikasi dapat bekerja dengan baik meskipun koneksi MongoDB gagal atau tidak tersedia.

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
- **MongoDB:** Aplikasi menggunakan MongoDB untuk menyimpan backup riwayat percakapan. Koneksi ke MongoDB dikonfigurasi melalui variabel `MONGO_URI` di file `.env`. Jika MongoDB tidak tersedia, aplikasi akan tetap berfungsi dengan normal menggunakan local storage saja.

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

- **`/sync-conversations` (POST)**  
  Endpoint untuk menyimpan percakapan dari local storage ke MongoDB.  
  **Parameter JSON:**  
  - `conversations`: Array berisi objek percakapan dari local storage.
  - `user_id`: ID pengguna (default: 'anonymous').

  **Response:**  
  - `status`: Status keberhasilan ('success', 'error', atau 'warning').
  - `message`: Pesan status atau error.

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

Aplikasi ini menggunakan MongoDB sebagai backup riwayat percakapan dengan pendekatan keamanan yang ditingkatkan. Berikut detail implementasinya:

### Arsitektur Sinkronisasi

Sistem menggunakan pendekatan **sinkronisasi satu arah** (one-way sync):

1. **Local Storage → MongoDB**:
   - Data percakapan disimpan di local storage browser pengguna
   - Secara otomatis di-backup ke MongoDB setiap kali percakapan diperbarui
   - Setiap percakapan diberi timestamp dan ID unik

2. **Tidak Ada Sinkronisasi Balik**:
   - Data tidak pernah mengalir dari MongoDB ke local storage
   - Setiap pengguna hanya melihat percakapan mereka sendiri
   - Jika local storage dihapus, pengguna memulai dengan riwayat kosong

### Struktur Data

Data percakapan disimpan dengan format berikut:

```javascript
{
  "id": "unique_conversation_id",
  "title": "Judul percakapan dari pesan pertama",
  "messages": [
    {"role": "user", "content": "Pesan pengguna"},
    {"role": "ai", "content": "Respons AI", "rawMarkdown": "Format mentah markdown"}
  ],
  "user_id": "anonymous",
  "last_synced": "2025-04-10T09:15:32.421Z",
  "created_at": "2025-04-10T09:00:00.000Z"
}
```

### Fault Tolerance

Sistem didesain untuk tetap berfungsi meskipun MongoDB tidak tersedia:

- Aplikasi tetap berjalan normal menggunakan local storage saja
- Percobaan sinkronisasi otomatis akan terus dilakukan saat koneksi tersedia kembali
- Kegagalan koneksi MongoDB tidak mempengaruhi pengalaman pengguna

### Pengaksesan Data (Admin)

Developer/admin dapat mengakses data percakapan melalui:

1. **MongoDB Atlas Dashboard**: Login ke MongoDB Atlas, pilih database `valiance_ai_db` dan collection `conversations`
2. **MongoDB Compass**: Hubungkan dengan URI MongoDB dan jelajahi data
3. **Query API**: Contoh query untuk menganalisis percakapan:

```javascript
// Ambil semua percakapan dari tanggal tertentu
db.conversations.find({
  "created_at": { $gte: ISODate("2025-04-10T00:00:00.000Z") }
})

// Hitung jumlah percakapan per hari
db.conversations.aggregate([
  { $group: { 
      _id: { $dateToString: { format: "%Y-%m-%d", date: "$created_at" } },
      count: { $sum: 1 }
    }
  },
  { $sort: { _id: 1 } }
])
```

## Keamanan Data

Sistem dirancang dengan fokus pada keamanan dan privasi data:

### Isolasi Data Pengguna

- **Sinkronisasi Satu Arah**: Data hanya mengalir dari local storage ke MongoDB, tidak sebaliknya
- **Tidak Ada Endpoint Pengambilan Data**: Endpoint `/get-conversations` dinonaktifkan untuk keamanan
- **Pemisahan Data Pengguna**: Setiap browser dan perangkat memiliki local storage terpisah

### Perlindungan Terhadap Eksposur Data

- **Tidak Ada Akses Silang**: Pengguna tidak dapat mengakses percakapan pengguna lain
- **Menghapus Local Storage**: Menghapus local storage hanya menghapus data di perangkat tersebut, tidak mempengaruhi data di perangkat lain
- **Backup Terisolasi**: Data di MongoDB hanya dapat diakses oleh admin sistem

### Praktik Keamanan Tambahan

- **Validasi Input**: Semua input dari pengguna divalidasi sebelum diproses
- **Error Handling**: Kesalahan ditangani dengan aman tanpa mengekspos informasi sensitif
- **Logging Aman**: Informasi sensitif tidak dicatat dalam log sistem

Pendekatan keamanan ini memastikan bahwa data pengguna terlindungi, privasi terjaga, dan sistem tetap beroperasi dengan baik bahkan dalam kondisi koneksi terbatas.

---
Copyright © 2025 Sekbid Multimedia Website Valiance
