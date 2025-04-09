import socket
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get MongoDB URI from env
uri = os.getenv("MONGO_URI")

print("=== [1] DNS Resolution Check ===")
host_to_test = "cluster0.oqipvob.mongodb.net"
try:
    ip = socket.gethostbyname(host_to_test)
    print(f"✅ DNS resolved: {host_to_test} -> {ip}")
except socket.gaierror as e:
    print(f"❌ DNS resolution failed: {e}")
    print("→ Coba ganti DNS server ke 1.1.1.1 atau 8.8.8.8 di /etc/resolv.conf")
    exit()

print("\n=== [2] MongoDB Connection Check ===")
if not uri:
    print("❌ MONGO_URI tidak ditemukan di .env")
    exit()

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ Berhasil konek ke MongoDB!")
except Exception as e:
    print(f"❌ Gagal konek ke MongoDB:\n{e}")
    print("→ Periksa whitelist IP, URI, dan apakah port 27017 dibuka")

print("\n=== Diagnostic Selesai ===")
