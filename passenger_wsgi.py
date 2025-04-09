import importlib.util
import os
import sys
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger('passenger_wsgi')

# Add the current directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))
logger.info(f"Working directory: {os.path.dirname(__file__)}")

try:
    # First try to load from cpanel_deploy.py (optimized for production)
    module_name = 'cpanel_deploy'
    module_path = os.path.join(os.path.dirname(__file__), f'{module_name}.py')
    
    if os.path.exists(module_path):
        logger.info(f"Loading from {module_path}")
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        cpanel_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cpanel_module)
        application = cpanel_module.application
        logger.info("Successfully loaded application from cpanel_deploy.py")
    else:
        # Fall back to main.py if cpanel_deploy.py doesn't exist
        logger.info("cpanel_deploy.py not found, falling back to main.py")
        module_name = 'main'
        module_path = os.path.join(os.path.dirname(__file__), f'{module_name}.py')
        
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        wsgi = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(wsgi)
        
        application = wsgi.app
        logger.info("Successfully loaded application from main.py")
        
except Exception as e:
    logger.error(f"Error loading application: {str(e)}", exc_info=True)
    # Create a simple error application
    def application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return [b'Application failed to load. Check server logs for details.'] 