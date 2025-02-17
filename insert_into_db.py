from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID  # If using PostgreSQL
import uuid
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('car_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Create base class for declarative models
Base = declarative_base()

# Load environment variables
load_dotenv(override=True)

db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME')

# Define the Car model
class Car(Base):
    __tablename__ = 'cars_cm2'
    
    uuid = Column(String(36), unique=True, primary_key=True, default=lambda: str(uuid.uuid4())) 
    url = Column(String(100))
    brand = Column(String(50))
    page = Column(Integer)
    timestamp = Column(DateTime)
    model = Column(String(50))
    year = Column(String(4))
    mileage = Column(String(30)) #a lot of junk data here, ideally it should be int but because of junk data we need string
    color = Column(String(50))
    price = Column(Float)

# Create database connection
engine = create_engine(f"postgresql://{db_user}:{db_password}@" \
                      f"{db_host}:{db_port}/{db_name}")
# For SQLite you can use: engine = create_engine('sqlite:///cars.db')

# Create tables if they don't exist
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine)
session = Session()

# Read JSON file
def import_cars_from_json(filename):
    with open(filename, 'r') as f:
        cars_data = json.load(f)

    # If the JSON contains a single object
    if isinstance(cars_data, dict):
        cars_data = [cars_data]

    # Keep track of successfully imported cars
    imported_count = 0

    for car_data in cars_data:
        for car in car_data:
            try:
                # Check if car with this UUID already exists
                existing_car = session.query(Car).filter_by(uuid=car.get('uuid')).first()
                
                if existing_car:
                    print(f"Car with UUID {car.get('uuid')} already exists, skipping")
                    continue
                
                # If no UUID provided, generate one
                if 'uuid' not in car:
                    car['uuid'] = str(uuid.uuid4())
                
                # Create Car instance
                new_car = Car(**car)
                session.add(new_car)
                imported_count += 1
                
            except Exception as e:
                print(f"Error processing car: {e}")
                continue

    try:
        # Commit the session
        session.commit()
        print(f"Successfully imported {imported_count} new cars")
        logger.info(f"Import completed. {imported_count} cars added")
    except Exception as e:
        session.rollback()
        print(f"Error importing data: {e}")
    finally:
        session.close()

# Usage
#bulk_import_cars('cars_list.json')
import_cars_from_json('car_list_motorgy.json')