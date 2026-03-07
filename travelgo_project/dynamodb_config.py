"""
DynamoDB Configuration for TravelGo
Manages all DynamoDB table operations for travel listings, seat availability, hotel details, and bookings.
Falls back to SQLite when AWS credentials are not available.
"""

import os
import sqlite3
from typing import Any, Dict, List, Optional
from decimal import Decimal
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, NoCredentialsError

# Configure DynamoDB
dynamodb: Optional[Any] = None

# Use SQLite fallback for local development
USE_SQLITE = os.environ.get('USE_SQLITE', 'true').lower() == 'true'
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'travelgo.db')

TABLE_NAMES = {
    'users': 'TravelGoUsers',
    'listings': 'TravelGoListings',
    'seat_availability': 'TravelGoSeatAvailability',
    'hotels': 'TravelGoHotels',
    'bookings': 'TravelGoBookings'
}


def get_dynamodb() -> Any:
    """Get DynamoDB resource - falls back to SQLite if AWS credentials are not available"""
    global dynamodb
    
    if USE_SQLITE:
        return None  # Will trigger SQLite mode
    
    if dynamodb is None:
        try:
            session = boto3.Session()
            dynamodb = session.resource('dynamodb')
            # Test connection
            dynamodb.meta.client.describe_endpoints()
        except (NoCredentialsError, ClientError) as e:
            print(f"AWS credentials not available: {e}")
            print("Falling back to SQLite database for local development")
            return None
    return dynamodb


def init_sqlite_db():
    """Initialize SQLite database with tables"""
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            UserID TEXT PRIMARY KEY,
            Name TEXT NOT NULL,
            Password TEXT NOT NULL,
            Logins INTEGER DEFAULT 0
        )
    ''')
    
    # Listings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            ListingID TEXT PRIMARY KEY,
            TransportType TEXT,
            Name TEXT,
            Source TEXT,
            Destination TEXT,
            Price REAL
        )
    ''')
    
    # Hotels table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hotels (
            HotelID TEXT PRIMARY KEY,
            Name TEXT,
            City TEXT,
            Type TEXT,
            Price REAL
        )
    ''')
    
    # Seat availability table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seat_availability (
            TransportID TEXT,
            Date TEXT,
            TransportType TEXT,
            AvailableSeats INTEGER,
            TotalSeats INTEGER,
            PRIMARY KEY (TransportID, Date)
        )
    ''')
    
    # Bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            BookingID TEXT PRIMARY KEY,
            UserID TEXT,
            Email TEXT,
            TransportID TEXT,
            Type TEXT,
            Source TEXT,
            Destination TEXT,
            Details TEXT,
            Seat TEXT,
            Price REAL,
            Date TEXT,
            PaymentMethod TEXT,
            PaymentReference TEXT,
            CreatedAt TEXT
        )
    ''')
    
    conn.commit()
    conn.close()


def seed_sqlite_data():
    """Seed initial data into SQLite"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Seed users
    cursor.execute('INSERT INTO users (UserID, Name, Password, Logins) VALUES (?, ?, ?, ?)',
                  ('test@travelgo.com', 'Test User', 'test123', 0))
    
    # Seed listings
    bus_data = [
        ("B1", "Bus", "Super Luxury Bus", "Hyderabad", "Bangalore", 800),
        ("B2", "Bus", "Express Bus", "Chennai", "Hyderabad", 700)
    ]
    train_data = [
        ("T1", "Train", "Rajdhani Express", "Hyderabad", "Delhi", 1500),
        ("T2", "Train", "Shatabdi Express", "Chennai", "Bangalore", 900)
    ]
    flight_data = [
        ("F1", "Flight", "Indigo 6E203", "Hyderabad", "Dubai", 8500),
        ("F2", "Flight", "Air India AI102", "Delhi", "Singapore", 9500)
    ]
    
    for bus in bus_data:
        cursor.execute('INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?)', bus)
    for train in train_data:
        cursor.execute('INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?)', train)
    for flight in flight_data:
        cursor.execute('INSERT INTO listings VALUES (?, ?, ?, ?, ?, ?)', flight)
    
    # Seed hotels
    hotel_data = [
        ("H1", "Grand Palace", "Chennai", "Luxury", 4000),
        ("H2", "Budget Inn", "Hyderabad", "Budget", 1500)
    ]
    for hotel in hotel_data:
        cursor.execute('INSERT INTO hotels VALUES (?, ?, ?, ?, ?)', hotel)
    
    # Seed seat availability
    today = datetime.now().strftime('%Y-%m-%d')
    for bus in bus_data:
        cursor.execute('INSERT INTO seat_availability VALUES (?, ?, ?, ?, ?)',
                      (bus[0], today, "Bus", 40, 40))
    for train in train_data:
        cursor.execute('INSERT INTO seat_availability VALUES (?, ?, ?, ?, ?)',
                      (train[0], today, "Train", 50, 50))
    for flight in flight_data:
        cursor.execute('INSERT INTO seat_availability VALUES (?, ?, ?, ?, ?)',
                      (flight[0], today, "Flight", 30, 30))
    
    conn.commit()
    conn.close()
    print("Seeded SQLite data")


def get_sqlite_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables() -> None:
    """Create all DynamoDB tables with keys and indexes"""
    if USE_SQLITE:
        init_sqlite_db()
        return
    
    db = get_dynamodb()
    if db is None:
        init_sqlite_db()
        return
    
    # USERS TABLE
    table = db.create_table(
        TableName=TABLE_NAMES['users'],
        KeySchema=[{'AttributeName': 'UserID', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'UserID', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()
    print(f"Created table: {TABLE_NAMES['users']}")
    
    # TRAVEL LISTINGS TABLE
    table = db.create_table(
        TableName=TABLE_NAMES['listings'],
        KeySchema=[{'AttributeName': 'ListingID', 'KeyType': 'HASH'}],
        AttributeDefinitions=[
            {'AttributeName': 'ListingID', 'AttributeType': 'S'},
            {'AttributeName': 'TransportType', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[{
            'IndexName': 'TransportTypeIndex',
            'KeySchema': [{'AttributeName': 'TransportType', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()
    print(f"Created table: {TABLE_NAMES['listings']}")
    
    # SEAT AVAILABILITY TABLE
    table = db.create_table(
        TableName=TABLE_NAMES['seat_availability'],
        KeySchema=[
            {'AttributeName': 'TransportID', 'KeyType': 'HASH'},
            {'AttributeName': 'Date', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'TransportID', 'AttributeType': 'S'},
            {'AttributeName': 'Date', 'AttributeType': 'S'},
            {'AttributeName': 'TransportType', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[{
            'IndexName': 'TransportTypeIndex',
            'KeySchema': [{'AttributeName': 'TransportType', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()
    print(f"Created table: {TABLE_NAMES['seat_availability']}")
    
    # HOTEL DETAILS TABLE
    table = db.create_table(
        TableName=TABLE_NAMES['hotels'],
        KeySchema=[{'AttributeName': 'HotelID', 'KeyType': 'HASH'}],
        AttributeDefinitions=[
            {'AttributeName': 'HotelID', 'AttributeType': 'S'},
            {'AttributeName': 'City', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[{
            'IndexName': 'CityIndex',
            'KeySchema': [{'AttributeName': 'City', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()
    print(f"Created table: {TABLE_NAMES['hotels']}")
    
    # BOOKINGS TABLE
    table = db.create_table(
        TableName=TABLE_NAMES['bookings'],
        KeySchema=[{'AttributeName': 'BookingID', 'KeyType': 'HASH'}],
        AttributeDefinitions=[
            {'AttributeName': 'BookingID', 'AttributeType': 'S'},
            {'AttributeName': 'UserID', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[{
            'IndexName': 'UserIDIndex',
            'KeySchema': [{'AttributeName': 'UserID', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'ALL'}
        }],
        BillingMode='PAY_PER_REQUEST'
    )
    table.wait_until_exists()
    print(f"Created table: {TABLE_NAMES['bookings']}")


def seed_initial_data() -> None:
    """Seed initial travel listings and hotel data"""
    if USE_SQLITE:
        seed_sqlite_data()
        return
    
    db = get_dynamodb()
    if db is None:
        seed_sqlite_data()
        return
    
    listings_table = db.Table(TABLE_NAMES['listings'])
    
    bus_data = [
        {"id": "B1", "name": "Super Luxury Bus", "source": "Hyderabad", "dest": "Bangalore", "price": 800},
        {"id": "B2", "name": "Express Bus", "source": "Chennai", "dest": "Hyderabad", "price": 700}
    ]
    
    train_data = [
        {"id": "T1", "name": "Rajdhani Express", "source": "Hyderabad", "dest": "Delhi", "price": 1500},
        {"id": "T2", "name": "Shatabdi Express", "source": "Chennai", "dest": "Bangalore", "price": 900}
    ]
    
    flight_data = [
        {"id": "F1", "name": "Indigo 6E203", "source": "Hyderabad", "dest": "Dubai", "price": 8500},
        {"id": "F2", "name": "Air India AI102", "source": "Delhi", "dest": "Singapore", "price": 9500}
    ]
    
    for bus in bus_data:
        listings_table.put_item(Item={
            'ListingID': bus['id'], 'TransportType': 'Bus', 'Name': bus['name'],
            'Source': bus['source'], 'Destination': bus['dest'], 'Price': Decimal(str(bus['price']))
        })
    
    for train in train_data:
        listings_table.put_item(Item={
            'ListingID': train['id'], 'TransportType': 'Train', 'Name': train['name'],
            'Source': train['source'], 'Destination': train['dest'], 'Price': Decimal(str(train['price']))
        })
    
    for flight in flight_data:
        listings_table.put_item(Item={
            'ListingID': flight['id'], 'TransportType': 'Flight', 'Name': flight['name'],
            'Source': flight['source'], 'Destination': flight['dest'], 'Price': Decimal(str(flight['price']))
        })
    
    print("Seeded travel listings")
    
    hotels_table = db.Table(TABLE_NAMES['hotels'])
    
    hotel_data = [
        {"id": "H1", "name": "Grand Palace", "city": "Chennai", "type": "Luxury", "price": 4000},
        {"id": "H2", "name": "Budget Inn", "city": "Hyderabad", "type": "Budget", "price": 1500}
    ]
    
    for hotel in hotel_data:
        hotels_table.put_item(Item={
            'HotelID': hotel['id'], 'Name': hotel['name'], 'City': hotel['city'],
            'Type': hotel['type'], 'Price': Decimal(str(hotel['price']))
        })
    
    print("Seeded hotel details")
    
    seats_table = db.Table(TABLE_NAMES['seat_availability'])
    today = datetime.now().strftime('%Y-%m-%d')
    
    for bus in bus_data:
        seats_table.put_item(Item={
            'TransportID': bus['id'], 'Date': today, 'TransportType': 'Bus',
            'AvailableSeats': 40, 'TotalSeats': 40
        })
    
    for train in train_data:
        seats_table.put_item(Item={
            'TransportID': train['id'], 'Date': today, 'TransportType': 'Train',
            'AvailableSeats': 50, 'TotalSeats': 50
        })
    
    for flight in flight_data:
        seats_table.put_item(Item={
            'TransportID': flight['id'], 'Date': today, 'TransportType': 'Flight',
            'AvailableSeats': 30, 'TotalSeats': 30
        })
    
    print("Seeded seat availability")
    
    users_table = db.Table(TABLE_NAMES['users'])
    users_table.put_item(Item={
        'UserID': 'test@travelgo.com', 'Name': 'Test User', 'Password': 'test123', 'Logins': 0
    })
    print("Seeded test user")


# ==================== USER OPERATIONS ====================

def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by email (UserID)"""
    # Try SQLite first
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE UserID = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'UserID': row[0], 'Name': row[1], 'Password': row[2], 'Logins': row[3]}
        return None
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['users'])
    response = table.get_item(Key={'UserID': user_id})
    return response.get('Item')

def create_user(email: str, name: str, password: str) -> bool:
    """Create new user"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (UserID, Name, Password, Logins) VALUES (?, ?, ?, ?)',
                      (email, name, password, 0))
        conn.commit()
        conn.close()
        return True
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['users'])
    table.put_item(Item={'UserID': email, 'Name': name, 'Password': password, 'Logins': 0})
    return True

def update_user_login(user_id: str) -> None:
    """Increment login count"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET Logins = Logins + 1 WHERE UserID = ?', (user_id,))
        conn.commit()
        conn.close()
        return
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['users'])
    table.update_item(
        Key={'UserID': user_id},
        UpdateExpression='SET #login = #login + :val',
        ExpressionAttributeNames={'#login': 'Logins'},
        ExpressionAttributeValues={':val': 1}
    )


# ==================== LISTING OPERATIONS ====================

def get_all_listings() -> List[Dict[str, Any]]:
    """Get all travel listings"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM listings')
        rows = cursor.fetchall()
        conn.close()
        return [{'ListingID': r[0], 'TransportType': r[1], 'Name': r[2], 'Source': r[3], 'Destination': r[4], 'Price': r[5]} for r in rows]
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['listings'])
    response = table.scan()
    return response.get('Items', [])

def get_listings_by_type(transport_type: str) -> List[Dict[str, Any]]:
    """Get listings by transport type (Bus, Train, Flight)"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM listings WHERE TransportType = ?', (transport_type,))
        rows = cursor.fetchall()
        conn.close()
        return [{'ListingID': r[0], 'TransportType': r[1], 'Name': r[2], 'Source': r[3], 'Destination': r[4], 'Price': r[5]} for r in rows]
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['listings'])
    response = table.query(
        IndexName='TransportTypeIndex',
        KeyConditionExpression=Key('TransportType').eq(transport_type)
    )
    return response.get('Items', [])

def get_listing(listing_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific listing"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM listings WHERE ListingID = ?', (listing_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'ListingID': row[0], 'TransportType': row[1], 'Name': row[2], 'Source': row[3], 'Destination': row[4], 'Price': row[5]}
        return None
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['listings'])
    response = table.get_item(Key={'ListingID': listing_id})
    return response.get('Item')


# ==================== SEAT AVAILABILITY OPERATIONS ====================

def get_seat_availability(transport_id: str, date: str) -> Optional[Dict[str, Any]]:
    """Get seat availability for a transport on a specific date"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM seat_availability WHERE TransportID = ? AND Date = ?', (transport_id, date))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'TransportID': row[0], 'Date': row[1], 'TransportType': row[2], 'AvailableSeats': row[3], 'TotalSeats': row[4]}
        return None
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['seat_availability'])
    response = table.get_item(Key={'TransportID': transport_id, 'Date': date})
    return response.get('Item')

def update_seat_availability(transport_id: str, date: str, seats_booked: int) -> None:
    """Decrement available seats after booking"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE seat_availability SET AvailableSeats = AvailableSeats - ? WHERE TransportID = ? AND Date = ?',
                      (seats_booked, transport_id, date))
        conn.commit()
        conn.close()
        return
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['seat_availability'])
    table.update_item(
        Key={'TransportID': transport_id, 'Date': date},
        UpdateExpression='SET AvailableSeats = AvailableSeats - :seats',
        ExpressionAttributeValues={':seats': seats_booked}
    )


# ==================== HOTEL OPERATIONS ====================

def get_all_hotels() -> List[Dict[str, Any]]:
    """Get all hotel details"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM hotels')
        rows = cursor.fetchall()
        conn.close()
        return [{'HotelID': r[0], 'Name': r[1], 'City': r[2], 'Type': r[3], 'Price': r[4]} for r in rows]
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['hotels'])
    response = table.scan()
    return response.get('Items', [])

def get_hotels_by_city(city: str) -> List[Dict[str, Any]]:
    """Get hotels by city"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM hotels WHERE City = ?', (city,))
        rows = cursor.fetchall()
        conn.close()
        return [{'HotelID': r[0], 'Name': r[1], 'City': r[2], 'Type': r[3], 'Price': r[4]} for r in rows]
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['hotels'])
    response = table.query(IndexName='CityIndex', KeyConditionExpression=Key('City').eq(city))
    return response.get('Items', [])

def get_hotel(hotel_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific hotel"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM hotels WHERE HotelID = ?', (hotel_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'HotelID': row[0], 'Name': row[1], 'City': row[2], 'Type': row[3], 'Price': row[4]}
        return None
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['hotels'])
    response = table.get_item(Key={'HotelID': hotel_id})
    return response.get('Item')


# ==================== BOOKING OPERATIONS ====================

def create_booking(
    booking_id: str, user_id: str, email: str, transport_id: str, listing_type: str,
    source: str, destination: str, details: str, seat: str, price: float,
    date: str, payment_method: str, payment_reference: str
) -> bool:
    """Create a new booking"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (booking_id, user_id, email, transport_id, listing_type, source, destination,
                       details, seat, price, date, payment_method, payment_reference, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['bookings'])
    table.put_item(Item={
        'BookingID': booking_id, 'UserID': user_id, 'Email': email,
        'TransportID': transport_id, 'Type': listing_type, 'Source': source,
        'Destination': destination, 'Details': details, 'Seat': seat,
        'Price': Decimal(str(price)), 'Date': date,
        'PaymentMethod': payment_method, 'PaymentReference': payment_reference,
        'CreatedAt': datetime.now().isoformat()
    })
    return True

def get_user_bookings(user_id: str) -> List[Dict[str, Any]]:
    """Get all bookings for a user"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bookings WHERE UserID = ?', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{'BookingID': r[0], 'UserID': r[1], 'Email': r[2], 'TransportID': r[3], 'Type': r[4],
                 'Source': r[5], 'Destination': r[6], 'Details': r[7], 'Seat': r[8], 'Price': r[9],
                 'Date': r[10], 'PaymentMethod': r[11], 'PaymentReference': r[12], 'CreatedAt': r[13]} for r in rows]
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['bookings'])
    response = table.query(IndexName='UserIDIndex', KeyConditionExpression=Key('UserID').eq(user_id))
    return response.get('Items', [])

def get_booking(booking_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific booking"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bookings WHERE BookingID = ?', (booking_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'BookingID': row[0], 'UserID': row[1], 'Email': row[2], 'TransportID': row[3], 'Type': row[4],
                    'Source': row[5], 'Destination': row[6], 'Details': row[7], 'Seat': row[8], 'Price': row[9],
                    'Date': row[10], 'PaymentMethod': row[11], 'PaymentReference': row[12], 'CreatedAt': row[13]}
        return None
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['bookings'])
    response = table.get_item(Key={'BookingID': booking_id})
    return response.get('Item')

def cancel_booking(booking_id: str) -> bool:
    """Cancel a booking by deleting it from the database"""
    if USE_SQLITE or get_dynamodb() is None:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM bookings WHERE BookingID = ?', (booking_id,))
        conn.commit()
        conn.close()
        return True
    
    db = get_dynamodb()
    table = db.Table(TABLE_NAMES['bookings'])
    table.delete_item(Key={'BookingID': booking_id})
    return True


# ==================== HELPER FUNCTIONS ====================

def convert_decimal_to_float(item: Any) -> Any:
    """Convert Decimal values to float for JSON serialization"""
    if isinstance(item, dict):
        return {k: convert_decimal_to_float(v) for k, v in item.items()}
    elif isinstance(item, list):
        return [convert_decimal_to_float(i) for i in item]
    elif isinstance(item, Decimal):
        return float(item)
    return item


if __name__ == '__main__':
    print("Setting up database...")
    create_tables()
    print("Seeding initial data...")
    seed_initial_data()
    print("Database setup complete!")

