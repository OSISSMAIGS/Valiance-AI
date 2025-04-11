import unittest
import os
import sys
import time
import psutil
import logging
import google.generativeai as genai
from pymongo import MongoClient
from dotenv import load_dotenv
import gc
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger('test_app')

# Load environment variables
load_dotenv()

class TestAppResources(unittest.TestCase):
    """Test suite to identify resource issues that might cause the application to crash."""
    
    def setUp(self):
        """Set up test environment."""
        self.process = psutil.Process(os.getpid())
        # Collect garbage to start with a clean slate
        gc.collect()
    
    def test_memory_usage_baseline(self):
        """Test the baseline memory usage of the application."""
        memory_before = self.process.memory_info().rss / 1024 / 1024  # Convert to MB
        logger.info(f"Baseline memory usage: {memory_before:.2f} MB")
        # This is just a baseline test, no assertion
    
    def test_mongodb_connection(self):
        """Test MongoDB connection and operations."""
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            self.skipTest("MongoDB URI not provided in environment variables")
        
        logger.info("Testing MongoDB connection...")
        try:
            # Connect with a timeout
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Verify connection
            client.admin.command('ping')
            logger.info("MongoDB connection successful")
            
            # Test insert, find, and delete operations
            db = client['test_db']
            collection = db['test_collection']
            
            # Insert a document
            result = collection.insert_one({"test": "data", "timestamp": time.time()})
            self.assertTrue(result.acknowledged)
            
            # Find the document
            doc = collection.find_one({"_id": result.inserted_id})
            self.assertIsNotNone(doc)
            
            # Delete the document
            delete_result = collection.delete_one({"_id": result.inserted_id})
            self.assertEqual(delete_result.deleted_count, 1)
            
            # Close connection
            client.close()
            
            logger.info("MongoDB operations completed successfully")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
            self.fail(f"MongoDB connection test failed: {str(e)}")
    
    def test_gemini_api(self):
        """Test the Gemini API connection and generation."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            self.skipTest("Gemini API key not provided in environment variables")
        
        logger.info("Testing Gemini API...")
        try:
            # Configure the API
            genai.configure(api_key=api_key)
            
            # Initialize the model
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Try a simple generation
            memory_before = self.process.memory_info().rss / 1024 / 1024  # Convert to MB
            logger.info(f"Memory before Gemini API call: {memory_before:.2f} MB")
            
            response = model.generate_content("Berikan salam singkat dalam bahasa Indonesia.")
            
            memory_after = self.process.memory_info().rss / 1024 / 1024  # Convert to MB
            logger.info(f"Memory after Gemini API call: {memory_after:.2f} MB")
            logger.info(f"Memory difference: {memory_after - memory_before:.2f} MB")
            
            self.assertIsNotNone(response.text)
            logger.info(f"Gemini API response: {response.text}")
            
            # Collect garbage to free memory
            gc.collect()
            
            logger.info("Gemini API test completed successfully")
        except Exception as e:
            logger.error(f"Gemini API test failed: {str(e)}")
            self.fail(f"Gemini API test failed: {str(e)}")
    
    def test_tuning_data_loading(self):
        """Test loading the tuning data file."""
        tuning_file = 'tuning_data.json'
        if not os.path.exists(tuning_file):
            self.skipTest(f"Tuning data file {tuning_file} not found")
        
        logger.info(f"Testing loading of tuning data from {tuning_file}...")
        try:
            memory_before = self.process.memory_info().rss / 1024 / 1024  # Convert to MB
            logger.info(f"Memory before loading tuning data: {memory_before:.2f} MB")
            
            # Load the tuning data
            with open(tuning_file, 'r', encoding='utf-8') as f:
                tuning_data = json.load(f)
            
            memory_after = self.process.memory_info().rss / 1024 / 1024  # Convert to MB
            logger.info(f"Memory after loading tuning data: {memory_after:.2f} MB")
            logger.info(f"Memory difference: {memory_after - memory_before:.2f} MB")
            
            self.assertIsInstance(tuning_data, list)
            logger.info(f"Tuning data loaded successfully, contains {len(tuning_data)} items")
            
            # Check if tuning data is too large
            tuning_data_size = os.path.getsize(tuning_file) / 1024 / 1024  # Convert to MB
            logger.info(f"Tuning data file size: {tuning_data_size:.2f} MB")
            
            # Free memory
            del tuning_data
            gc.collect()
            
            logger.info("Tuning data test completed successfully")
        except Exception as e:
            logger.error(f"Tuning data loading test failed: {str(e)}")
            self.fail(f"Tuning data loading test failed: {str(e)}")
    
    def test_memory_leak_simulation(self):
        """Simulate a potential memory leak by repeatedly calling Gemini API."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            self.skipTest("Gemini API key not provided in environment variables")
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Initialize the model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        logger.info("Testing for potential memory leaks during repeated API calls...")
        
        memory_readings = []
        iterations = 5  # Reduced number to avoid timeout
        
        for i in range(iterations):
            memory_before = self.process.memory_info().rss / 1024 / 1024
            memory_readings.append(memory_before)
            
            logger.info(f"Iteration {i+1}/{iterations}, Memory: {memory_before:.2f} MB")
            
            # Generate content with a typical prompt that would be used in your app
            prompt = (
                "Berikan informasi tentang OSIS di sekolah.\n\n"
                "Harap berikan respons dalam format Markdown."
            )
            
            try:
                response = model.generate_content(prompt)
                # Force garbage collection after each call
                gc.collect()
                time.sleep(1)  # Brief pause to allow system to stabilize
            except Exception as e:
                logger.error(f"API call failed on iteration {i+1}: {str(e)}")
                break
        
        # Check memory growth pattern
        if len(memory_readings) > 1:
            final_memory = self.process.memory_info().rss / 1024 / 1024
            memory_readings.append(final_memory)
            
            logger.info(f"Memory readings across iterations: {memory_readings}")
            logger.info(f"Final memory usage: {final_memory:.2f} MB")
            
            # Determine if there's a consistent memory increase
            is_increasing = all(memory_readings[i] <= memory_readings[i+1] for i in range(len(memory_readings)-1))
            if is_increasing:
                logger.warning("Memory usage shows an increasing trend, potential memory leak")
            else:
                logger.info("Memory usage pattern does not indicate a significant leak")

    def test_cpu_usage(self):
        """Test CPU usage during various operations."""
        logger.info("Testing CPU usage...")
        
        # Test CPU during a CPU-intensive operation
        def cpu_intensive_task():
            # Simple CPU-intensive calculation
            result = 0
            for i in range(1000000):
                result += i
            return result
        
        # Measure CPU usage during the task
        cpu_percent_before = self.process.cpu_percent(interval=0.1)
        start_time = time.time()
        cpu_intensive_task()
        cpu_percent_after = self.process.cpu_percent(interval=0.1)
        end_time = time.time()
        
        logger.info(f"CPU usage before: {cpu_percent_before}%")
        logger.info(f"CPU usage after: {cpu_percent_after}%")
        logger.info(f"Task duration: {end_time - start_time:.2f} seconds")

if __name__ == '__main__':
    unittest.main() 