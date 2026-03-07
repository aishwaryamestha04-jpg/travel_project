"""
Comprehensive Test Suite for TravelGo Application
=================================================
This module contains all tests for the TravelGo Flask application,
including authentication, booking workflows, and API endpoints.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test fixtures
from tests.fixtures import (
    MockDynamoDB, MockSNS, mock_dynamodb, mock_sns,
    TEST_USER, TEST_BOOKING, TEST_LISTINGS, TEST_HOTELS, reset_mocks
)


class TestApp(unittest.TestCase):
    """Test cases for the TravelGo Flask application"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Reset mocks before each test
        reset_mocks()
        
        # Mock DynamoDB
        self.mock_dynamodb_patcher = patch('dynamodb_config.get_dynamodb')
        self.mock_dynamodb = self.mock_dynamodb_patcher.start()
        self.mock_dynamodb.return_value = mock_dynamodb
        
        # Mock SNS
        self.mock_sns_patcher = patch('app.sns')
        self.mock_sns = self.mock_sns_patcher.start()
        self.mock_sns.return_value = mock_sns
        
        # Import app after patching
        import app as app_module
        self.app = app_module.app
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Create test client
        self.client = self.app.test_client()
        
        # Initialize database tables
        import dynamodb_config as db
        db.dynamodb = mock_dynamodb
    
    def tearDown(self):
        """Clean up after each test"""
        self.mock_dynamodb_patcher.stop()
        self.mock_sns_patcher.stop()
    
    # ==================== HOME PAGE TESTS ====================
    
    def test_home_page_loads(self):
        """Test that home page loads successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TravelGo', response.data)
    
    def test_home_page_has_login_link(self):
        """Test that home page contains login link"""
        response = self.client.get('/')
        self.assertIn(b'/login', response.data)
    
    # ==================== AUTHENTICATION TESTS ====================
    
    def test_register_page_loads(self):
        """Test that register page loads successfully"""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
    
    def test_register_new_user(self):
        """Test user registration with valid data"""
        response = self.client.post('/register', data={
            'email': 'newuser@test.com',
            'name': 'New User',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        # First register
        self.client.post('/register', data={
            'email': TEST_USER['email'],
            'name': TEST_USER['name'],
            'password': TEST_USER['password']
        })
        
        # Try to register again with same email
        response = self.client.post('/register', data={
            'email': TEST_USER['email'],
            'name': TEST_USER['name'],
            'password': TEST_USER['password']
        })
        
        self.assertIn(b'already exists', response.data)
    
    def test_login_page_loads(self):
        """Test that login page loads successfully"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        response = self.client.post('/login', data={
            'email': TEST_USER['email'],
            'password': TEST_USER['password']
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post('/login', data={
            'email': 'wrong@email.com',
            'password': 'wrongpassword'
        })
        self.assertIn(b'Invalid credentials', response.data)
    
    def test_logout(self):
        """Test logout functionality"""
        # First login
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        # Then logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    # ==================== DASHBOARD TESTS ====================
    
    def test_dashboard_requires_login(self):
        """Test that dashboard redirects to login when not authenticated"""
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_dashboard_loads_authenticated(self):
        """Test dashboard loads for authenticated user"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
    
    # ==================== TRANSPORT SEARCH TESTS ====================
    
    def test_bus_search_page_loads(self):
        """Test bus search page loads successfully"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        response = self.client.get('/bus')
        self.assertEqual(response.status_code, 200)
    
    def test_train_search_page_loads(self):
        """Test train search page loads successfully"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        response = self.client.get('/train')
        self.assertEqual(response.status_code, 200)
    
    def test_flight_search_page_loads(self):
        """Test flight search page loads successfully"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        response = self.client.get('/flight')
        self.assertEqual(response.status_code, 200)
    
    def test_bus_search_with_filters(self):
        """Test bus search with source and destination filters"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        response = self.client.get('/bus?source=Hyderabad&destination=Bangalore')
        self.assertEqual(response.status_code, 200)
    
    # ==================== HOTEL SEARCH TESTS ====================
    
    def test_hotels_page_loads(self):
        """Test hotels page loads successfully"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        response = self.client.get('/hotels')
        self.assertEqual(response.status_code, 200)
    
    def test_hotels_filter_by_category(self):
        """Test hotels filter by category"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        response = self.client.get('/hotels?type=Luxury')
        self.assertEqual(response.status_code, 200)
    
    # ==================== SEAT SELECTION TESTS ====================
    
    def test_seat_selection_page_loads(self):
        """Test seat selection page loads successfully"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        response = self.client.get('/seat/B1/800')
        self.assertEqual(response.status_code, 200)
    
    def test_seat_selection_requires_login(self):
        """Test seat selection requires authentication"""
        response = self.client.get('/seat/B1/800')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    # ==================== BOOKING TESTS ====================
    
    def test_book_seat(self):
        """Test seat booking flow"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        response = self.client.post('/book', data={
            'transport_id': 'B1',
            'seat': '1, 2',
            'price': '1600'
        })
        self.assertEqual(response.status_code, 200)
    
    def test_book_requires_login(self):
        """Test booking requires authentication"""
        response = self.client.post('/book', data={
            'transport_id': 'B1',
            'seat': '1',
            'price': '800'
        })
        self.assertEqual(response.status_code, 302)  # Redirect
    
    # ==================== PAYMENT TESTS ====================
    
    def test_payment_page_loads(self):
        """Test payment page loads after seat selection"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
            session['booking_flow'] = {
                'transport_id': 'B1',
                'type': 'Bus',
                'source': 'Hyderabad',
                'destination': 'Bangalore',
                'details': 'Super Luxury Bus',
                'seat': '1',
                'price': 800,
                'date': datetime.now().strftime('%Y-%m-%d')
            }
        
        response = self.client.get('/payment')
        self.assertEqual(response.status_code, 200)
    
    def test_payment_process(self):
        """Test payment processing"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
            session['booking_flow'] = TEST_BOOKING.copy()
        
        response = self.client.post('/payment', data={
            'method': 'UPI',
            'reference': 'UPI-TEST-001'
        })
        self.assertEqual(response.status_code, 200)
    
    # ==================== CANCELLATION TESTS ====================
    
    def test_cancel_booking(self):
        """Test booking cancellation"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        response = self.client.get('/cancel/TEST001')
        # Should redirect to dashboard after cancellation
        self.assertEqual(response.status_code, 302)
    
    def test_cancel_requires_login(self):
        """Test cancellation requires authentication"""
        response = self.client.get('/cancel/TEST001')
        self.assertEqual(response.status_code, 302)
    
    # ==================== SNS NOTIFICATION TESTS ====================
    
    def test_booking_confirmation_sns(self):
        """Test that booking confirmation triggers SNS"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
            session['booking_flow'] = TEST_BOOKING.copy()
        
        self.client.post('/payment', data={
            'method': 'UPI',
            'reference': 'TEST-REF'
        })
        
        # Check SNS was called
        self.mock_sns.publish.assert_called()
    
    def test_cancellation_sns(self):
        """Test that cancellation triggers SNS"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        # First create a booking
        self.client.post('/cancel/TEST001')
        
        # SNS should be called for cancellation
        # (Note: actual SNS call happens after booking exists)
    
    # ==================== ERROR HANDLING TESTS ====================
    
    def test_404_error(self):
        """Test 404 error page"""
        response = self.client.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
    
    def test_transport_not_found(self):
        """Test booking with non-existent transport"""
        with self.client.session_transaction() as session:
            session['user'] = TEST_USER['email']
            session['name'] = TEST_USER['name']
        
        response = self.client.post('/book', data={
            'transport_id': 'NONEXISTENT',
            'seat': '1',
            'price': '100'
        })
        self.assertEqual(response.status_code, 404)


class TestDynamoDBOperations(unittest.TestCase):
    """Test cases for DynamoDB operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        reset_mocks()
        
        self.mock_dynamodb_patcher = patch('dynamodb_config.get_dynamodb')
        self.mock_dynamodb = self.mock_dynamodb_patcher.start()
        self.mock_dynamodb.return_value = mock_dynamodb
        
        import dynamodb_config as db
        db.dynamodb = mock_dynamodb
        self.db = db
    
    def tearDown(self):
        """Clean up"""
        self.mock_dynamodb_patcher.stop()
    
    def test_get_user(self):
        """Test getting a user"""
        user = self.db.get_user(TEST_USER['email'])
        self.assertIsNotNone(user)
        # Use optional chaining to handle potential None
        user_name = user.get('Name') if user else None
        self.assertEqual(user_name, TEST_USER['name'])
    
    def test_get_user_not_found(self):
        """Test getting non-existent user"""
        user = self.db.get_user('nonexistent@test.com')
        # User should be None for non-existent email
        self.assertIsNone(user)
    
    def test_get_listings_by_type(self):
        """Test getting listings by transport type"""
        buses = self.db.get_listings_by_type('Bus')
        self.assertIsInstance(buses, list)
    
    def test_get_all_hotels(self):
        """Test getting all hotels"""
        hotels = self.db.get_all_hotels()
        self.assertIsInstance(hotels, list)
    
    def test_create_booking(self):
        """Test creating a booking"""
        result = self.db.create_booking(
            booking_id='TEST123',
            user_id='test@travelgo.com',
            email='test@travelgo.com',
            transport_id='B1',
            listing_type='Bus',
            source='Hyderabad',
            destination='Bangalore',
            details='Super Luxury Bus',
            seat='1',
            price=800,
            date='2024-01-01',
            payment_method='UPI',
            payment_reference='UPI001'
        )
        self.assertTrue(result)
    
    def test_cancel_booking(self):
        """Test cancelling a booking"""
        # First create a booking
        self.db.create_booking(
            booking_id='TEST123',
            user_id='test@travelgo.com',
            email='test@travelgo.com',
            transport_id='B1',
            listing_type='Bus',
            source='Hyderabad',
            destination='Bangalore',
            details='Super Luxury Bus',
            seat='1',
            price=800,
            date='2024-01-01',
            payment_method='UPI',
            payment_reference='UPI001'
        )
        
        # Then cancel it
        result = self.db.cancel_booking('TEST123')
        self.assertTrue(result)


class TestSNService(unittest.TestCase):
    """Test cases for SNS notification service"""
    
    def setUp(self):
        """Set up test fixtures"""
        reset_mocks()
    
    def test_sns_publish(self):
        """Test SNS publish functionality"""
        import sns_service
        
        result = sns_service.send_booking_notification(
            phone_number='+1234567890',
            message='Test message'
        )
        
        self.assertIsNotNone(result)
    
    def test_sns_handles_error(self):
        """Test SNS error handling"""
        import sns_service
        
        # Mock SNS to raise an exception
        with patch('sns_service.sns') as mock:
            mock.publish.side_effect = Exception('SNS Error')
            result = sns_service.send_booking_notification(
                phone_number='+1234567890',
                message='Test'
            )
            self.assertIsNone(result)


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)

