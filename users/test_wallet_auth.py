"""
Test suite for wallet-based authentication endpoints.

Run with: python manage.py test users.test_wallet_auth
"""

from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import uuid

User = get_user_model()


class WalletAuthenticationTests(TestCase):
    """Test wallet-based authentication flow"""
    
    def setUp(self):
        """Set up test client and test data"""
        self.client = APIClient()
        self.test_wallet = "SP2J6ZY48GV1EZ5V2V5RB9MP66SW86PYKKNRV9EJ7"
        self.test_signature = "0x" + "a" * 128  # Mock signature (long enough to pass validation)
        
    def tearDown(self):
        """Clean up cache after each test"""
        cache.clear()
        User.objects.all().delete()
    
    # ============================================
    # Test get_auth_message endpoint
    # ============================================
    
    def test_get_auth_message_success(self):
        """Test successful nonce generation"""
        response = self.client.post(
            '/api/users/get_auth_message/',
            {'wallet_address': self.test_wallet},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('nonce', response.data)
        self.assertIn(self.test_wallet, response.data['message'])
        
        # Verify nonce is stored in cache
        cached_nonce = cache.get(f'auth_nonce_{self.test_wallet}')
        self.assertEqual(cached_nonce, response.data['nonce'])
    
    def test_get_auth_message_missing_wallet(self):
        """Test error when wallet_address is missing"""
        response = self.client.post('/api/users/get_auth_message/', {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_get_auth_message_invalid_wallet_format(self):
        """Test error when wallet address has invalid format"""
        response = self.client.post(
            '/api/users/get_auth_message/',
            {'wallet_address': 'INVALID_WALLET'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    # ============================================
    # Test login_or_register endpoint
    # ============================================
    
    def test_login_or_register_new_user(self):
        """Test authentication creates new user and issues tokens"""
        # First get auth message
        auth_response = self.client.post(
            '/api/users/get_auth_message/',
            {'wallet_address': self.test_wallet},
            format='json'
        )
        message = auth_response.data['message']
        
        # Then authenticate
        response = self.client.post(
            '/api/users/login_or_register/',
            {
                'wallet_address': self.test_wallet,
                'signed_message': self.test_signature,
                'original_message': message
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_new'])
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        
        # Verify user was created
        user = User.objects.get(stacks_address=self.test_wallet)
        self.assertIsNotNone(user)
        self.assertEqual(user.stacks_address, self.test_wallet)
        self.assertTrue(user.username.startswith('user_'))
    
    def test_login_or_register_existing_user(self):
        """Test authentication for existing user"""
        # Create existing user
        existing_user = User.objects.create(
            username='existing_user',
            stacks_address=self.test_wallet,
            role='creator'
        )
        
        # Get auth message
        auth_response = self.client.post(
            '/api/users/get_auth_message/',
            {'wallet_address': self.test_wallet},
            format='json'
        )
        message = auth_response.data['message']
        
        # Authenticate
        response = self.client.post(
            '/api/users/login_or_register/',
            {
                'wallet_address': self.test_wallet,
                'signed_message': self.test_signature,
                'original_message': message
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_new'])
        self.assertEqual(response.data['user']['id'], existing_user.id)
        self.assertEqual(response.data['user']['username'], 'existing_user')
        self.assertIn('tokens', response.data)
    
    def test_login_or_register_missing_fields(self):
        """Test error when required fields are missing"""
        response = self.client.post(
            '/api/users/login_or_register/',
            {'wallet_address': self.test_wallet},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_login_or_register_expired_nonce(self):
        """Test error when nonce has expired"""
        response = self.client.post(
            '/api/users/login_or_register/',
            {
                'wallet_address': self.test_wallet,
                'signed_message': self.test_signature,
                'original_message': 'expired message'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_login_or_register_invalid_nonce(self):
        """Test error when nonce doesn't match"""
        # Get auth message
        auth_response = self.client.post(
            '/api/users/get_auth_message/',
            {'wallet_address': self.test_wallet},
            format='json'
        )
        
        # Try to authenticate with wrong nonce in message
        response = self.client.post(
            '/api/users/login_or_register/',
            {
                'wallet_address': self.test_wallet,
                'signed_message': self.test_signature,
                'original_message': 'Message with wrong nonce'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_login_or_register_nonce_deleted_after_use(self):
        """Test that nonce is deleted after successful auth (prevents replay)"""
        # Get auth message
        auth_response = self.client.post(
            '/api/users/get_auth_message/',
            {'wallet_address': self.test_wallet},
            format='json'
        )
        message = auth_response.data['message']
        
        # Authenticate successfully
        self.client.post(
            '/api/users/login_or_register/',
            {
                'wallet_address': self.test_wallet,
                'signed_message': self.test_signature,
                'original_message': message
            },
            format='json'
        )
        
        # Try to reuse same message (replay attack)
        response = self.client.post(
            '/api/users/login_or_register/',
            {
                'wallet_address': self.test_wallet,
                'signed_message': self.test_signature,
                'original_message': message
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    # ============================================
    # Test complete_setup endpoint
    # ============================================
    
    def test_complete_setup_success(self):
        """Test successful profile completion"""
        # Create user and get tokens
        user = User.objects.create(
            username='temp_user',
            stacks_address=self.test_wallet
        )
        
        # Authenticate to get token
        self.client.force_authenticate(user=user)
        
        # Complete setup
        response = self.client.patch(
            '/api/users/complete_setup/',
            {
                'username': 'my_custom_username',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'creator',
                'bio': 'Test bio'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'my_custom_username')
        self.assertEqual(response.data['user']['first_name'], 'John')
        self.assertEqual(response.data['user']['role'], 'creator')
        
        # Verify changes in database
        user.refresh_from_db()
        self.assertEqual(user.username, 'my_custom_username')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.bio, 'Test bio')
    
    def test_complete_setup_requires_authentication(self):
        """Test that complete_setup requires authentication"""
        response = self.client.patch(
            '/api/users/complete_setup/',
            {'username': 'new_username'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_complete_setup_duplicate_username(self):
        """Test error when username is already taken"""
        # Create two users
        user1 = User.objects.create(
            username='existing_username',
            stacks_address='SP111111111111111111111111111111111111111'
        )
        user2 = User.objects.create(
            username='temp_user',
            stacks_address=self.test_wallet
        )
        
        # Authenticate as user2
        self.client.force_authenticate(user=user2)
        
        # Try to use user1's username
        response = self.client.patch(
            '/api/users/complete_setup/',
            {'username': 'existing_username'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_complete_setup_partial_update(self):
        """Test that partial updates work (only provided fields are updated)"""
        user = User.objects.create(
            username='original_username',
            stacks_address=self.test_wallet,
            bio='Original bio'
        )
        
        self.client.force_authenticate(user=user)
        
        # Update only bio
        response = self.client.patch(
            '/api/users/complete_setup/',
            {'bio': 'Updated bio'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        user.refresh_from_db()
        self.assertEqual(user.username, 'original_username')  # Unchanged
        self.assertEqual(user.bio, 'Updated bio')  # Changed
    
    # ============================================
    # Integration tests
    # ============================================
    
    def test_full_auth_flow_new_user(self):
        """Test complete authentication flow for new user"""
        # Step 1: Get auth message
        step1 = self.client.post(
            '/api/users/get_auth_message/',
            {'wallet_address': self.test_wallet},
            format='json'
        )
        self.assertEqual(step1.status_code, status.HTTP_200_OK)
        
        # Step 2: Authenticate (creates user)
        step2 = self.client.post(
            '/api/users/login_or_register/',
            {
                'wallet_address': self.test_wallet,
                'signed_message': self.test_signature,
                'original_message': step1.data['message']
            },
            format='json'
        )
        self.assertEqual(step2.status_code, status.HTTP_200_OK)
        self.assertTrue(step2.data['is_new'])
        access_token = step2.data['tokens']['access']
        
        # Step 3: Complete profile setup
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        step3 = self.client.patch(
            '/api/users/complete_setup/',
            {
                'username': 'complete_user',
                'role': 'creator',
                'bio': 'Integration test user'
            },
            format='json'
        )
        self.assertEqual(step3.status_code, status.HTTP_200_OK)
        self.assertEqual(step3.data['user']['username'], 'complete_user')
        
        # Verify user in database
        user = User.objects.get(stacks_address=self.test_wallet)
        self.assertEqual(user.username, 'complete_user')
        self.assertEqual(user.role, 'creator')
        self.assertEqual(user.bio, 'Integration test user')
    
    def test_full_auth_flow_existing_user(self):
        """Test complete authentication flow for existing user"""
        # Create existing user
        User.objects.create(
            username='veteran_user',
            stacks_address=self.test_wallet,
            role='creator',
            bio='Existing user bio'
        )
        
        # Step 1: Get auth message
        step1 = self.client.post(
            '/api/users/get_auth_message/',
            {'wallet_address': self.test_wallet},
            format='json'
        )
        
        # Step 2: Authenticate (should NOT create new user)
        initial_count = User.objects.count()
        step2 = self.client.post(
            '/api/users/login_or_register/',
            {
                'wallet_address': self.test_wallet,
                'signed_message': self.test_signature,
                'original_message': step1.data['message']
            },
            format='json'
        )
        
        self.assertEqual(step2.status_code, status.HTTP_200_OK)
        self.assertFalse(step2.data['is_new'])
        self.assertEqual(User.objects.count(), initial_count)  # No new user created
        self.assertEqual(step2.data['user']['username'], 'veteran_user')


class WalletAuthSecurityTests(TestCase):
    """Test security features of wallet authentication"""
    
    def setUp(self):
        self.client = APIClient()
        self.test_wallet = "SP2J6ZY48GV1EZ5V2V5RB9MP66SW86PYKKNRV9EJ7"
        self.test_signature = "0x" + "a" * 128
    
    def tearDown(self):
        cache.clear()
        User.objects.all().delete()
    
    def test_nonce_expiration(self):
        """Test that nonces expire after 5 minutes"""
        # Manually set an expired nonce
        cache.set(f'auth_nonce_{self.test_wallet}', 'expired_nonce', 1)
        
        # Wait for expiration (simulate)
        cache.delete(f'auth_nonce_{self.test_wallet}')
        
        # Try to authenticate with expired nonce
        response = self.client.post(
            '/api/users/login_or_register/',
            {
                'wallet_address': self.test_wallet,
                'signed_message': self.test_signature,
                'original_message': 'Message with expired_nonce'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_invalid_signature_format(self):
        """Test that invalid signature format is rejected"""
        # Get valid auth message
        auth_response = self.client.post(
            '/api/users/get_auth_message/',
            {'wallet_address': self.test_wallet},
            format='json'
        )
        
        # Try with invalid signature (too short)
        response = self.client.post(
            '/api/users/login_or_register/',
            {
                'wallet_address': self.test_wallet,
                'signed_message': '0x123',  # Too short
                'original_message': auth_response.data['message']
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_wallet_address_uniqueness(self):
        """Test that wallet addresses must be unique"""
        User.objects.create(
            username='user1',
            stacks_address=self.test_wallet
        )
        
        # Try to create another user with same wallet
        with self.assertRaises(Exception):  # Should raise IntegrityError
            User.objects.create(
                username='user2',
                stacks_address=self.test_wallet
            )


if __name__ == '__main__':
    import django
    import sys
    import os
    
    # Setup Django
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deorganized.settings')
    django.setup()
    
    # Run tests
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["users.test_wallet_auth"])
    
    if failures:
        sys.exit(1)
