"""
Booking Workflow Tests for TravelGo
====================================
This module tests the complete booking workflow from search to ticket generation.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.fixtures import (
    mock_dynamodb, mock_sns, TEST_USER, TEST_BOOKING, reset_mocks
)


class TestBookingWorkflow(unittest.TestCase):
    """Test complete booking workflows"""
    
    def setUp(self):
        """Set up test fixtures"""
        reset_mocks()
        
        self.mock_dynamodb_patcher = patch('dynamodb_config.get_dynamodb')
        self.mock_dynamodb = self.mock_dynamodb_patcher.start()
        self.mock_dynamodb.return_value = mock_dynamodb
        
        self.mock_sns_patcher = patch('app.sns')
        self.mock_sns = self.mock_sns_patcher.start()
        self.mock_sns.return_value = mock_sns
        
        import app as app_module
        self.app = app_module.app
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-key'
        self.client = self.app.test_client()
        
        import dynamodb_config as db
        db.dynamodb = mock_dynamodb
    
    def tearDown(self):
        """Clean up"""
        self.mock_dynamodb_patcher.stop()
        self.mock_sns_patcher.stop()
    
    def test_complete_bus_booking_workflow(self):
        """Test complete bus booking workflow"""
        # Step 1: Login
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        # Step 2: Search for bus
        response = self.client.get('/bus')
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Select seat
        response = self.client.get('/seat/B1/800')
        self.assertEqual(response.status_code, 200)
        
        # Step 4: Book seat
        response = self.client.post('/book', data={
            'transport_id': 'B1',
            'seat': '1, 2',
            'price': '1600'
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 5: Process payment
        response = self.client.post('/payment', data={
            'method': 'UPI',
            'reference': 'UPI-TEST-123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify booking was created
        import dynamodb_config as db
        bookings = db.get_user_bookings(TEST_USER['email'])
        self.assertGreater(len(bookings), 0)
    
    def test_complete_hotel_booking_workflow(self):
        """Test complete hotel booking workflow"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        # Search hotels
        response = self.client.get('/hotels?type=Luxury')
        self.assertEqual(response.status_code, 200)
        
        # Select hotel and book
        response = self.client.post('/book', data={
            'transport_id': 'H1',
            'seat': '1',
            'price': '4000'
        })
        self.assertEqual(response.status_code, 200)
        
        # Process payment
        response = self.client.post('/payment', data={
            'method': 'Credit Card',
            'reference': 'CC-TEST-456'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_booking_cancellation_workflow(self):
        """Test booking cancellation workflow"""
        # First create a booking
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        # Create booking
        self.client.post('/book', data={
            'transport_id': 'B1',
            'seat': '5',
            'price': '800'
        })
        
        self.client.post('/payment', data={
            'method': 'UPI',
            'reference': 'UPI-CANCEL-TEST'
        })
        
        # Get bookings
        import dynamodb_config as db
        bookings = db.get_user_bookings(TEST_USER['email'])
        
        if bookings:
            booking_item = bookings[0]
            booking_id = str(booking_item.get('BookingID')) if booking_item.get('BookingID') else 'TEST001'
            
            # Cancel the booking
            response = self.client.get(f'/cancel/{booking_id}', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Verify booking is cancelled
            cancelled_booking = db.get_booking(booking_id)
            # After cancellation, booking should not exist
            self.assertIsNone(cancelled_booking)
    
    def test_seat_availability_update(self):
        """Test seat availability is updated after booking"""
        import dynamodb_config as db
        
        today = datetime.now().strftime('%Y-%m-%d')
        initial_seats = db.get_seat_availability('B1', today)
        initial_count = initial_seats.get('AvailableSeats', 40) if initial_seats else 40
        
        # Create booking
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        self.client.post('/book', data={
            'transport_id': 'B1',
            'seat': '1',
            'price': '800'
        })
        
        self.client.post('/payment', data={
            'method': 'UPI',
            'reference': 'SEAT-TEST'
        })
        
        # Check seat availability updated
        updated_seats = db.get_seat_availability('B1', today)
        updated_count = updated_seats.get('AvailableSeats', 40) if updated_seats else 40
        
        self.assertLess(updated_count, initial_count)
    
    def test_multi_seat_booking(self):
        """Test booking multiple seats at once"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        # Book multiple seats
        response = self.client.post('/book', data={
            'transport_id': 'B1',
            'seat': '1, 2, 3, 4, 5',
            'price': '4000'
        })
        self.assertEqual(response.status_code, 200)
        
        # Process payment
        response = self.client.post('/payment', data={
            'method': 'Net Banking',
            'reference': 'MULTI-SEAT-TEST'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)


class TestSearchFilters(unittest.TestCase):
    """Test search and filter functionality"""
    
    def setUp(self):
        reset_mocks()
        self.mock_dynamodb_patcher = patch('dynamodb_config.get_dynamodb')
        self.mock_dynamodb = self.mock_dynamodb_patcher.start()
        self.mock_dynamodb.return_value = mock_dynamodb
        
        import app as app_module
        self.app = app_module.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        import dynamodb_config as db
        db.dynamodb = mock_dynamodb
    
    def tearDown(self):
        self.mock_dynamodb_patcher.stop()
    
    def test_bus_filter_by_source(self):
        """Test bus filter by source city"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        response = self.client.get('/bus?source=Hyderabad')
        self.assertEqual(response.status_code, 200)
    
    def test_bus_filter_by_destination(self):
        """Test bus filter by destination city"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        response = self.client.get('/bus?destination=Bangalore')
        self.assertEqual(response.status_code, 200)
    
    def test_hotel_filter_by_type(self):
        """Test hotel filter by type (Luxury, Budget, etc.)"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        # Test Luxury filter
        response = self.client.get('/hotels?type=Luxury')
        self.assertEqual(response.status_code, 200)
        
        # Test Budget filter
        response = self.client.get('/hotels?type=Budget')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)

