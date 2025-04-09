import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the MongoDB URI from environment variables
MONGO_URI = os.getenv('MONGO_URI')

print("==== MongoDB Connection Test ====")
print(f"Connecting with URI starting with: {MONGO_URI[:25]}...")

try:
    # Connect to MongoDB
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    
    # Check connection
    client.admin.command('ping')
    
    print("✅ Connection successful!")
    
    # List available databases
    print("\nAvailable databases:")
    for db_name in client.list_database_names():
        print(f" - {db_name}")
    
    # Show available collections in the target database
    db_name = 'valiance_ai_db'
    db = client[db_name]
    print(f"\nCollections in {db_name}:")
    for collection in db.list_collection_names():
        print(f" - {collection}")
    
except Exception as e:
    print("❌ Connection failed!")
    print(f"Error: {str(e)}")
    print("\nTroubleshooting tips:")
    print(" 1. Check username and password in the connection string")
    print(" 2. Ensure your IP address is whitelisted in MongoDB Atlas")
    print(" 3. Verify network connection and firewall settings")
    print(" 4. Check that the user has appropriate database access roles")
    print(" 5. Ensure the cluster is running and accessible")
    
    # Specific checks for common errors
    error_str = str(e).lower()
    if "authentication failed" in error_str:
        print("\nAuthentication Error Detected:")
        print(" - Double-check username and password")
        print(" - Ensure user exists and has proper permissions")
    elif "timeout" in error_str:
        print("\nTimeout Error Detected:")
        print(" - Check network connectivity")
        print(" - Verify IP whitelist in MongoDB Atlas")
    elif "ssl" in error_str:
        print("\nSSL Error Detected:")
        print(" - Check SSL configuration")
        print(" - Ensure you're using the correct connection string format")

print("\n==== Test Complete ====") 