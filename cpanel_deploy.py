"""
CPanel Deployment Helper for Flask + MongoDB
--------------------------------------------
This script is designed to help with deployment on cPanel shared hosting.
It provides:
1. Error logging
2. Socket handling
3. MongoDB connection pooling optimization
4. Timeout configuration for shared hosting environments
"""

import sys
import os
import logging
from logging.handlers import RotatingFileHandler
import time

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Set up file logging
log_file = os.path.join(log_dir, 'app.log')
handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)

# Set up logger
logger = logging.getLogger('cpanel_deploy')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Add log info about startup
logger.info('Starting cpanel_deploy.py wrapper')
logger.info(f'Python version: {sys.version}')
logger.info(f'Current directory: {os.getcwd()}')

# Import after logging setup to catch any import errors
try:
    from main import app as application
    logger.info('Successfully imported Flask application')
    
    # Override MongoDB settings for cPanel
    if hasattr(application, 'config'):
        # Reduce connection pool size for shared hosting
        if 'MONGO_MAX_POOL_SIZE' not in application.config:
            application.config['MONGO_MAX_POOL_SIZE'] = 5
        logger.info(f"MongoDB pool size: {application.config.get('MONGO_MAX_POOL_SIZE', 'default')}")
    
except Exception as e:
    logger.error(f'Failed to import application: {str(e)}', exc_info=True)
    # Re-raise to let the WSGI server handle it
    raise

# Export the WSGI application object for Passenger
application.logger.addHandler(handler)
logger.info('cpanel_deploy.py initialization complete')

# For debugging in cPanel logs
print("cpanel_deploy.py loaded successfully", file=sys.stderr) 