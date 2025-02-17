from dotenv import load_dotenv
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv(override=True)

def verify_env_variables():
    """Verify and display database connection settings"""
    # Get environment variables
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME')
    
    # Log the values (mask password)
    logging.debug(f"DB_USER: {db_user}")
    logging.debug(f"DB_PASSWORD: {'*' * len(str(db_password)) if db_password else None}")
    logging.debug(f"DB_HOST: {db_host}")
    logging.debug(f"DB_PORT: {db_port}")
    logging.debug(f"DB_NAME: {db_name}")
    
    # Check for missing variables
    missing_vars = []
    if not db_user:
        missing_vars.append('DB_USER')
    if not db_password:
        missing_vars.append('DB_PASSWORD')
    if not db_host:
        missing_vars.append('DB_HOST')
    if not db_name:
        missing_vars.append('DB_NAME')
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
    
    return {
        'DB_USER': db_user,
        'DB_PASSWORD': db_password,
        'DB_HOST': db_host,
        'DB_PORT': db_port,
        'DB_NAME': db_name
    }

def test_database_connection():
    """Test the database connection"""
    try:
        # Get and verify environment variables
        env_vars = verify_env_variables()
        
        # Construct database URL
        database_url = f"postgresql://{env_vars['DB_USER']}:{env_vars['DB_PASSWORD']}@" \
                      f"{env_vars['DB_HOST']}:{env_vars['DB_PORT']}/{env_vars['DB_NAME']}"
        
        logging.info("Attempting to connect to database...")
        
        # Try to connect
        engine = create_engine(database_url)
        with engine.connect() as connection:
            logging.info("Successfully connected to database!")
        
        return True
        
    except SQLAlchemyError as e:
        logging.error(f"Database connection error: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        test_database_connection()
    except Exception as e:
        logging.error(f"Setup failed: {str(e)}")