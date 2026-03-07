"""
Logging Configuration for TravelGo
===================================
This module configures logging for the TravelGo application,
with support for both local file logging and CloudWatch.
"""

import os
import logging
import logging.handlers
from logging.handlers import RotatingFileHandler

# Create logger
logger = logging.getLogger('travelgo')
logger.setLevel(logging.INFO)

# Log format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_file_logging(log_dir='/var/log/travelgo'):
    """Setup file-based logging"""
    
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Access log
    access_handler = RotatingFileHandler(
        os.path.join(log_dir, 'access.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Error log
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Application log
    app_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    app_handler.setLevel(logging.DEBUG)
    app_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    
    # Add handlers
    logger.addHandler(access_handler)
    logger.addHandler(error_handler)
    logger.addHandler(app_handler)
    
    return logger


def setup_console_logging():
    """Setup console logging for development"""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console_handler)
    return logger


def get_logger(name=None):
    """Get a logger instance"""
    if name:
        return logging.getLogger(f'travelgo.{name}')
    return logger


# ==================== REQUEST LOGGING ====================

class RequestLogger:
    """Middleware for logging HTTP requests"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger('request')
    
    def __call__(self, environ, start_response):
        # Log request
        self.logger.info(
            f"{environ['REQUEST_METHOD']} {environ['PATH_INFO']} "
            f"from {environ.get('REMOTE_ADDR', 'unknown')}"
        )
        
        # Capture response
        def logging_start_response(status, headers, exc_info=None):
            self.logger.info(f"Response: {status}")
            return start_response(status, headers, exc_info)
        
        return self.app(environ, logging_start_response)


# ==================== PERFORMANCE LOGGING ====================

class PerformanceLogger:
    """Middleware for logging request performance"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger('performance')
    
    def __call__(self, environ, start_response):
        import time
        
        start_time = time.time()
        
        def logging_start_response(status, headers, exc_info=None):
            duration = (time.time() - start_time) * 1000  # ms
            self.logger.info(
                f"{environ['REQUEST_METHOD']} {environ['PATH_INFO']} "
                f"completed in {duration:.2f}ms - {status}"
            )
            return start_response(status, headers, exc_info)
        
        return self.app(environ, logging_start_response)


# ==================== ERROR LOGGING ====================

class ErrorLogger:
    """Middleware for logging errors and exceptions"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger('error')
    
    def __call__(self, environ, start_response):
        try:
            return self.app(environ, start_response)
        except Exception as e:
            self.logger.exception(
                f"Error processing {environ['REQUEST_METHOD']} {environ['PATH_INFO']}: {e}"
            )
            raise


# ==================== INITIALIZATION ====================

def init_logging():
    """Initialize logging configuration"""
    env = os.environ.get('FLASK_ENV', 'production')
    
    if env == 'development':
        # Development: console logging
        setup_console_logging()
    else:
        # Production: file + CloudWatch logging
        try:
            setup_file_logging()
        except Exception as e:
            # Fall back to console if file logging fails
            setup_console_logging()
            logging.warning(f"Could not setup file logging: {e}")
    
    # Also log to CloudWatch if enabled
    try:
        from cloudwatch_config import put_log_events
        # CloudWatch logging is enabled via cloudwatch_config
    except ImportError:
        pass
    
    logger.info(f"Logging initialized for {env} environment")
    return logger


# Export logger
logger = init_logging()


if __name__ == '__main__':
    # Test logging
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message")
    print("Logging configured successfully!")

