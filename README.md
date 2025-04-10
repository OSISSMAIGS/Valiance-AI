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
- [Admin Dashboard](#admin-dashboard)
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
- **Admin Dashboard:** Panel admin dengan keamanan login untuk monitoring data percakapan dan pengguna secara real-time.

## Persyaratan

- **Python 3.7+**
- **Flask**
- **google-generativeai**
- **python-dotenv**
- **pymongo**
- **bcrypt** (untuk enkripsi password admin)
- **Akun MongoDB Atlas** (untuk penyimpanan data chat dan akun admin)

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
   SECRET_KEY=your_flask_secret_key_here
   ADMIN_SETUP_KEY=your_admin_setup_secret_key_here
   ```

## Konfigurasi

- **Gemini API:** Aplikasi mengkonfigurasi Gemini API dengan membaca kunci API dari file `.env`.
- **Tuning Data:** Data tuning disimpan di file `tuning_data.json` yang berfungsi untuk menyimpan contoh-contoh pertanyaan dan respons. Data tuning ini digunakan sebagai referensi saat membangun prompt untuk Gemini API.
- **MongoDB:** Aplikasi menggunakan MongoDB untuk menyimpan backup riwayat percakapan. Koneksi ke MongoDB dikonfigurasi melalui variabel `MONGO_URI` di file `.env`. Jika MongoDB tidak tersedia, aplikasi akan tetap berfungsi dengan normal menggunakan local storage saja.
- **Secret Keys:** Gunakan `SECRET_KEY` untuk keamanan sesi Flask dan `ADMIN_SETUP_KEY` untuk proses pembuatan akun admin pertama kali.

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

- **`/admin/login` (GET, POST)**  
  Halaman login untuk admin dashboard.

- **`/admin` (GET)**  
  Admin dashboard untuk melihat dan mengelola data percakapan (memerlukan otentikasi).

- **`/admin/logout` (GET)**  
  Endpoint untuk logout dari admin dashboard.

- **`/setup-admin` (POST)**  
  Endpoint untuk membuat akun admin baru.  
  **Parameter JSON:**  
  - `username`: Username admin.
  - `password`: Password admin.
  - `secret_key`: Secret key yang telah dikonfigurasi di file .env.

  **Response:**  
  - `status`: Status keberhasilan ('success' atau 'error').
  - `message`: Pesan status atau error.

## Struktur Proyek

```
valiance-ai-agent/
├── app.py                  # File utama aplikasi Flask
├── tuning_data.json        # File untuk menyimpan dan mengupdate data tuning
├── templates/
│   ├── index.html          # Template halaman utama
│   ├── layout.html         # Template layout umum
│   └── admin/              # Template untuk admin dashboard
│       ├── login.html      # Halaman login admin
│       └── dashboard.html  # Dashboard admin untuk monitoring
├── static/
│   ├── css/
│   │   ├── style.css       # File stylesheet untuk chat
│   │   └── admin.css       # File stylesheet untuk admin dashboard
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

## Admin Dashboard

Admin Dashboard adalah antarmuka khusus untuk administrator yang memungkinkan pemantauan dan pengelolaan data percakapan secara terpusat. Berikut adalah fitur-fitur utama Admin Dashboard:

### Fitur Admin Dashboard

- **Login Aman**: Sistem autentikasi dengan enkripsi password menggunakan bcrypt
- **Monitoring Percakapan**: Melihat seluruh riwayat percakapan pengguna yang tersimpan di MongoDB
- **Statistik Real-time**: Menampilkan jumlah total percakapan, jumlah pengguna unik, dan waktu sinkronisasi terakhir
- **Pencarian Data**: Pencarian cepat di seluruh database berdasarkan konten percakapan, judul, atau ID pengguna
- **Render Markdown**: Menampilkan respons AI dalam format Markdown yang dirender dengan benar
- **Copy Markdown**: Kemampuan untuk menyalin konten Markdown mentah dari respons AI
- **Tampilan Responsif**: Desain UI yang bekerja dengan baik di desktop maupun perangkat mobile
- **Keamanan Tingkat Tinggi**: Proteksi akses dengan session management dan login required

### Cara Mengakses Admin Dashboard

1. **Membuat Akun Admin**:
   Untuk membuat akun admin pertama kali, kirim request POST ke endpoint `/setup-admin` dengan format:

   ```json
   {
     "username": "admin_username_anda",
     "password": "password_anda",
     "secret_key": "kunci_secret_dari_env_file"
   }
   ```

   Pastikan `secret_key` sesuai dengan nilai `ADMIN_SETUP_KEY` di file `.env`.

2. **Login ke Dashboard**:
   - Buka `/admin/login` di browser
   - Masukkan username dan password yang telah dibuat
   - Setelah berhasil login, Anda akan diarahkan ke dashboard admin

3. **Menggunakan Dashboard**:
   - Lihat statistik di bagian atas dashboard
   - Telusuri daftar percakapan yang tersinkronisasi
   - Klik pada judul percakapan untuk memperluas dan melihat detail pesan
   - Gunakan kotak pencarian untuk menemukan percakapan spesifik

### Keamanan Admin Dashboard

- Password admin di-hash menggunakan bcrypt sebelum disimpan ke database
- Session Flask digunakan untuk mengelola status login dengan aman
- Secret key diperlukan untuk membuat akun admin, mencegah akses tidak sah
- Semua route admin dilindungi dengan decorator `admin_login_required`
- Tidak ada data sensitif yang ditampilkan di URL atau disimpan di client-side

## Keamanan Data

Sistem dirancang dengan fokus pada keamanan dan privasi data:

### Isolasi Data Pengguna

- **Sinkronisasi Satu Arah**: Data hanya mengalir dari local storage ke MongoDB, tidak sebaliknya
- **Tidak Ada Endpoint Pengambilan Data**: Endpoint `/get-conversations` dinonaktifkan untuk keamanan
- **Pemisahan Data Pengguna**: Setiap browser dan perangkat memiliki local storage terpisah

### Perlindungan Terhadap Eksposur Data

- **Tidak Ada Akses Silang**: Pengguna tidak dapat mengakses percakapan pengguna lain
- **Menghapus Local Storage**: Menghapus local storage hanya menghapus data di perangkat tersebut, tidak mempengaruhi data di perangkat lain
- **Backup Terisolasi**: Data di MongoDB hanya dapat diakses oleh admin sistem melalui dashboard admin yang dilindungi login

### Praktik Keamanan Tambahan

- **Validasi Input**: Semua input dari pengguna divalidasi sebelum diproses
- **Error Handling**: Kesalahan ditangani dengan aman tanpa mengekspos informasi sensitif
- **Logging Aman**: Informasi sensitif tidak dicatat dalam log sistem
- **Enkripsi Password**: Password admin di-hash menggunakan bcrypt
- **Secret Keys**: Penggunaan secret keys untuk autentikasi dan pembuatan akun admin

Pendekatan keamanan ini memastikan bahwa data pengguna terlindungi, privasi terjaga, dan sistem tetap beroperasi dengan baik bahkan dalam kondisi koneksi terbatas.

---
Copyright © 2025 Sekbid Multimedia Website Valiance
