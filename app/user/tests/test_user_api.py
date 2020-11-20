from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')

class TestPublicUserAPI(TestCase):

    def create_user(self,**params):
        return get_user_model().objects.create_user(**params)

    def setUp(self):
        self.client = APIClient()
        self.basic_user_payload = {'email':'test@site.com','password':'password123', 'name':'new_user'}

    def test_create_user_success(self):

        res = self.client.post(CREATE_USER_URL, self.basic_user_payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(self.basic_user_payload['password']))
        self.assertNotIn(self.basic_user_payload['password'], res.data)

    def test_create_user_that_exists(self):
        self.create_user(**self.basic_user_payload)
        res = self.client.post(CREATE_USER_URL, self.basic_user_payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_shot_password(self):
        self.basic_user_payload['password'] = '123'
        res = self.client.post(CREATE_USER_URL, self.basic_user_payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter( email = self.basic_user_payload['email']).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        self.create_user(**self.basic_user_payload)
        res = self.client.post(TOKEN_URL, self.basic_user_payload)
        self.assertIn('token',res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_for_user_with_invalid_credentials(self):
        self.create_user(**self.basic_user_payload)
        self.basic_user_payload['password'] = '321'
        res = self.client.post(TOKEN_URL, self.basic_user_payload)
        self.assertNotIn('token',res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        res = self.client.post(TOKEN_URL, self.basic_user_payload)
        self.assertNotIn('token',res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        self.basic_user_payload['email'] = 'invalidadValue'
        self.basic_user_payload['password'] = '1234'
        res = self.client.post(TOKEN_URL, self.basic_user_payload)
        self.assertNotIn('token',res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


        self.basic_user_payload['email'] = 'valid@asd.com'
        self.basic_user_payload['password'] = ''#missing value
        res = self.client.post(TOKEN_URL, self.basic_user_payload)
        self.assertNotIn('token',res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
