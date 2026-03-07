"""
Test Fixtures and Mock Utilities for TravelGo
==============================================
This module provides fixtures and mock classes for testing the TravelGo
application without connecting to actual AWS services.
"""

import os
import sys
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockDynamoDB:
    """Mock DynamoDB for testing"""
    
    def __init__(self):
        self.tables = {}
        self._init_tables()
    
    def _init_tables(self):
        """Initialize mock tables"""
        # Users table
        self.tables['TravelGoUsers'] = {
            'test@travelgo.com': {
                'UserID': 'test@travelgo.com',
                'Name': 'Test User',
                'Password': 'test123',
                'Logins': 0
            }
        }
        
        # Listings table
        self.tables['TravelGoListings'] = {
            'B1': {
                'ListingID': 'B1',
                'TransportType': 'Bus',
                'Name': 'Super Luxury Bus',
                'Source': 'Hyderabad',
                'Destination': 'Bangalore',
                'Price': 800
            },
            'T1': {
                'ListingID': 'T1',
                'TransportType': 'Train',
                'Name': 'Rajdhani Express',
                'Source': 'Hyderabad',
                'Destination': 'Delhi',
                'Price': 1500
            },
            'F1': {
                'ListingID': 'F1',
                'TransportType': 'Flight',
                'Name': 'Indigo 6E203',
                'Source': 'Hyderabad',
                'Destination': 'Dubai',
                'Price': 8500
            }
        }
        
        # Hotels table
        self.tables['TravelGoHotels'] = {
            'H1': {
                'HotelID': 'H1',
                'Name': 'Grand Palace',
                'City': 'Chennai',
                'Type': 'Luxury',
                'Price': 4000
            }
        }
        
        # Bookings table
        self.tables['TravelGoBookings'] = {}
        
        # Seat availability table
        self.tables['TravelGoSeatAvailability'] = {}
        
        # Seed seat availability
        today = datetime.now().strftime('%Y-%m-%d')
        for listing_id in ['B1', 'T1', 'F1']:
            self.tables['TravelGoSeatAvailability'][(listing_id, today)] = {
                'TransportID': listing_id,
                'Date': today,
                'AvailableSeats': 40,
                'TotalSeats': 40
            }
    
    def resource(self, service):
        if service == 'dynamodb':
            return self
        return Mock()
    
    def Table(self, table_name):
        return MockTable(table_name, self.tables.get(table_name, {}))


class MockTable:
    """Mock DynamoDB Table"""
    
    def __init__(self, name, data):
        self.name = name
        self.data = data
    
    def put_item(self, Item):
        key_field = self._get_key_field()
        if key_field in Item:
            self.data[Item[key_field]] = Item
    
    def get_item(self, Key):
        key_field = self._get_key_field()
        key_value = Key.get(key_field)
        
        # Handle composite keys
        if isinstance(key_value, dict):
            # For tables with composite keys
            key_str = tuple(key_value.values())
            return {'Item': self.data.get(key_str)}
        
        return {'Item': self.data.get(key_value)}
    
    def scan(self):
        return {'Items': list(self.data.values())}
    
    def query(self, IndexName=None, KeyConditionExpression=None, **kwargs):
        # Simplified query - return all items for now
        return {'Items': list(self.data.values())}
    
    def update_item(self, Key, UpdateExpression=None, ExpressionAttributeNames=None, ExpressionAttributeValues=None, **kwargs):
        key_field = self._get_key_field()
        key_value = Key.get(key_field)
        
        if key_value in self.data and ExpressionAttributeValues:
            for attr, value in ExpressionAttributeValues.items():
                if ':seats' in attr:
                    current = self.data[key_value].get('AvailableSeats', 0)
                    self.data[key_value]['AvailableSeats'] = current - value
    
    def delete_item(self, Key):
        key_field = self._get_key_field()
        key_value = Key.get(key_field)
        if key_value in self.data:
            del self.data[key_value]
    
    def _get_key_field(self):
        """Get the primary key field name for each table"""
        key_mapping = {
            'TravelGoUsers': 'UserID',
            'TravelGoListings': 'ListingID',
            'TravelGoHotels': 'HotelID',
            'TravelGoBookings': 'BookingID',
            'TravelGoSeatAvailability': 'TransportID'
        }
        return key_mapping.get(self.name, 'id')


class MockSNS:
    """Mock AWS SNS for testing"""
    
    def __init__(self):
        self.published_messages = []
    
    def publish(self, TopicArn=None, PhoneNumber=None, Message=None, Subject=None):
        self.published_messages.append({
            'TopicArn': TopicArn,
            'PhoneNumber': PhoneNumber,
            'Message': Message,
            'Subject': Subject,
            'MessageId': f'msg-{len(self.published_messages) + 1}'
        })
        return {'MessageId': f'msg-{len(self.published_messages)}'}
    
    def get_published_messages(self):
        return self.published_messages


# Global mock instances
mock_dynamodb = MockDynamoDB()
mock_sns = MockSNS()


def get_mock_dynamodb():
    """Get the mock DynamoDB instance"""
    return mock_dynamodb


def get_mock_sns():
    """Get the mock SNS instance"""
    return mock_sns


def reset_mocks():
    """Reset all mock data"""
    global mock_dynamodb, mock_sns
    mock_dynamodb = MockDynamoDB()
    mock_sns = MockSNS()


# Test user credentials
TEST_USER = {
    'email': 'test@travelgo.com',
    'name': 'Test User',
    'password': 'test123'
}

# Test booking data
TEST_BOOKING = {
    'booking_id': 'TEST001',
    'user_id': 'test@travelgo.com',
    'email': 'test@travelgo.com',
    'transport_id': 'B1',
    'type': 'Bus',
    'source': 'Hyderabad',
    'destination': 'Bangalore',
    'details': 'Super Luxury Bus',
    'seat': '1, 2',
    'price': 1600,
    'date': datetime.now().strftime('%Y-%m-%d'),
    'payment_method': 'UPI',
    'payment_reference': 'TEST-UPI-001'
}

# Test transport listings
TEST_LISTINGS = {
    'bus': [
        {'ListingID': 'B1', 'Name': 'Super Luxury Bus', 'Source': 'Hyderabad', 'Destination': 'Bangalore', 'Price': 800, 'TransportType': 'Bus'},
        {'ListingID': 'B2', 'Name': 'Express Bus', 'Source': 'Chennai', 'Destination': 'Hyderabad', 'Price': 700, 'TransportType': 'Bus'}
    ],
    'train': [
        {'ListingID': 'T1', 'Name': 'Rajdhani Express', 'Source': 'Hyderabad', 'Destination': 'Delhi', 'Price': 1500, 'TransportType': 'Train'}
    ],
    'flight': [
        {'ListingID': 'F1', 'Name': 'Indigo 6E203', 'Source': 'Hyderabad', 'Destination': 'Dubai', 'Price': 8500, 'TransportType': 'Flight'}
    ]
}

# Test hotels
TEST_HOTELS = [
    {'HotelID': 'H1', 'Name': 'Grand Palace', 'City': 'Chennai', 'Type': 'Luxury', 'Price': 4000},
    {'HotelID': 'H2', 'Name': 'Budget Inn', 'City': 'Hyderabad', 'Type': 'Budget', 'Price': 1500}
]

