"""
MongoDB Configuration Helper
This module provides helper functions for connecting to MongoDB Atlas
with fallback options and detailed error reporting.
"""

import os
import socket
import urllib.parse
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_connection_options():
    """Returns a dictionary of MongoDB connection options"""
    return {
        'serverSelectionTimeoutMS': 5000,
        'connectTimeoutMS': 5000,
        'socketTimeoutMS': 10000,
        'connect': True,
        'retryWrites': True,
        'w': 'majority'
    }

def get_mongo_uri():
    """Get the MongoDB URI with fallbacks"""
    # First try the environment variable
    uri = os.getenv('MONGO_URI')
    if not uri:
        # No URI found
        return None, "MONGO_URI environment variable not found"
    
    return uri, None

def get_connection_variants(base_uri):
    """Get different variants of the connection string to try"""
    variants = [base_uri]
    
    # If we're using mongodb+srv, add a standard mongodb:// variant
    if base_uri.startswith('mongodb+srv://'):
        # Parse the URI to get the components
        # mongodb+srv://username:password@host/database?options
        try:
            # Remove the srv part for parsing
            uri_parts = base_uri.replace('mongodb+srv://', '')
            # Split auth and host
            if '@' in uri_parts:
                auth, rest = uri_parts.split('@', 1)
                if '/' in rest:
                    host, rest = rest.split('/', 1)
                    if '?' in rest:
                        db, options = rest.split('?', 1)
                        # Create standard connection string
                        standard_uri = f"mongodb://{auth}@{host}/{db}?{options}&authSource=admin"
                        variants.append(standard_uri)
        except Exception:
            pass  # If parsing fails, just stick with the original
    
    return variants

def get_mongo_client():
    """
    Get a MongoDB client instance with fallback options
    Returns:
        tuple: (client, db, collection, error_message)
    """
    uri, error = get_mongo_uri()
    if error:
        return None, None, None, error
    
    # Get connection options
    options = get_connection_options()
    
    # Get connection string variants to try
    connection_variants = get_connection_variants(uri)
    
    # Try each variant
    last_error = None
    for variant_uri in connection_variants:
        try:
            print(f"Trying to connect with URI starting with: {variant_uri[:25]}...")
            client = MongoClient(variant_uri, **options)
            
            # Test the connection
            client.admin.command('ping')
            
            # Get the database and collection
            db = client['valiance_ai_db']
            collection = db['chat_history']
            
            print(f"MongoDB connection successful with {variant_uri[:25]}...")
            return client, db, collection, None
            
        except Exception as e:
            last_error = str(e)
            print(f"Connection attempt failed: {last_error}")
    
    return None, None, None, last_error

def check_mongo_availability(host_str):
    """
    Check if the MongoDB host is reachable via socket
    Args:
        host_str: Host string from MongoDB URI
    Returns:
        tuple: (is_reachable, error_message)
    """
    try:
        # Extract host and port
        if ':' in host_str:
            host, port_str = host_str.split(':', 1)
            port = int(port_str)
        else:
            host = host_str
            port = 27017  # Default MongoDB port
        
        # Try to connect to the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)  # 2 second timeout
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return True, None
        else:
            return False, f"Host {host}:{port} is not reachable (error code: {result})"
            
    except Exception as e:
        return False, f"Error checking host availability: {str(e)}"

def get_detailed_connection_info():
    """
    Get detailed information about the MongoDB connection for diagnostics
    Returns:
        dict: Connection information and diagnostics
    """
    info = {
        'uri_exists': False,
        'connection_tests': [],
        'host_checks': [],
        'variants_tested': []
    }
    
    # Check if URI exists
    uri, error = get_mongo_uri()
    if error:
        info['error'] = error
        return info
    
    info['uri_exists'] = True
    
    # Parse URI to get host for connectivity check
    try:
        if uri.startswith('mongodb+srv://'):
            # mongodb+srv://username:password@host/database
            host_part = uri.split('@', 1)[1].split('/', 1)[0]
        elif uri.startswith('mongodb://'):
            # mongodb://username:password@host:port/database
            host_part = uri.split('@', 1)[1].split('/', 1)[0]
        else:
            host_part = None
            
        if host_part:
            reachable, reach_error = check_mongo_availability(host_part)
            info['host_checks'].append({
                'host': host_part,
                'reachable': reachable,
                'error': reach_error
            })
    except Exception as e:
        info['host_parse_error'] = str(e)
    
    # Try connection variants
    connection_variants = get_connection_variants(uri)
    options = get_connection_options()
    
    for variant in connection_variants:
        info['variants_tested'].append(variant[:25] + '...')
        
        try:
            client = MongoClient(variant, serverSelectionTimeoutMS=2000)
            client.admin.command('ping')
            info['connection_tests'].append({
                'variant': variant[:25] + '...',
                'success': True
            })
        except Exception as e:
            info['connection_tests'].append({
                'variant': variant[:25] + '...',
                'success': False,
                'error': str(e)
            })
    
    return info 