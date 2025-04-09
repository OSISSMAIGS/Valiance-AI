#!/bin/bash
# MongoDB Debug Script for cPanel
# Usage: bash mongo_debug.sh

echo "======== MongoDB Connectivity Diagnostic ========"
echo "Checking Python and environment..."

# Check Python version
python_version=$(python3 -V 2>&1)
echo "Python version: $python_version"

# Check if pymongo is installed
pymongo_version=$(python3 -c "import pymongo; print('PyMongo version:', pymongo.__version__)" 2>&1)
echo $pymongo_version

# Check DNS resolution for MongoDB Atlas
echo -e "\nDNS resolution check:"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  # Linux
  mongo_host=$(grep -o '@[^/]*' .env | sed 's/@//g' | head -1)
  if [ -n "$mongo_host" ]; then
    echo "MongoDB host from .env: $mongo_host"
    host_result=$(host $mongo_host 2>&1)
    echo "$host_result"
  else
    echo "Could not find MongoDB host in .env file"
  fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
  # Mac
  mongo_host=$(grep -o '@[^/]*' .env | sed 's/@//g' | head -1)
  if [ -n "$mongo_host" ]; then
    echo "MongoDB host from .env: $mongo_host"
    dig_result=$(dig +short $mongo_host 2>&1)
    echo "$dig_result"
  else
    echo "Could not find MongoDB host in .env file"
  fi
else
  echo "Unsupported OS for DNS check, skipping"
fi

# Run Python MongoDB diagnostic test
echo -e "\nRunning Python MongoDB connection test..."
python3 test_mongodb.py

# Check for common cPanel issues
echo -e "\nChecking for common cPanel configuration issues:"

# Check if the .htaccess file has proper configuration
if [ -f ".htaccess" ]; then
  echo "✓ .htaccess file exists"
  if grep -q "passenger_wsgi.py" .htaccess; then
    echo "✓ .htaccess contains passenger_wsgi.py reference"
  else
    echo "✗ .htaccess might be missing proper Passenger configuration"
  fi
else
  echo "✗ .htaccess file not found"
fi

# Check if necessary directories exist
if [ -d "logs" ]; then
  echo "✓ logs directory exists"
  echo "Recent log entries:"
  tail -n 5 logs/app.log 2>/dev/null || echo "  No logs found"
else
  echo "Creating logs directory..."
  mkdir -p logs
fi

echo -e "\n========= Diagnostic Complete ==========="
echo "If you're still having issues, please check:"
echo "1. MongoDB Atlas IP whitelist settings"
echo "2. MongoDB user credentials"
echo "3. cPanel Python version configuration"
echo "4. Timeout settings in mongodb_config.py" 