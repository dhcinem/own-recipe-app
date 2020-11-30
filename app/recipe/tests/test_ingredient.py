from django.test import TestCase

# Create your tests here.
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')

class PublicTagsAPI(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_loguin_required(self):
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class TestPrivateTagAPI(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@site.com',
            'password123'
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        Ingredient.objects.create(user=self.user, name="Curcuma")
        Ingredient.objects.create(user=self.user, name="Pimienta")

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limit_to_user(self):
        anotherUser = get_user_model().objects.create_user("anotherUser@asdmcl.com", "password2")
        ingredient = Ingredient.objects.create(user=self.user, name='Sal')
        Ingredient.objects.create(user=anotherUser, name='Sal marina')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successfull(self):
        payload = {'name':'Test ingredient'}
        self.client.post(INGREDIENT_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        payload = {'name':''}
        res = self.client.post(INGREDIENT_URL,payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
