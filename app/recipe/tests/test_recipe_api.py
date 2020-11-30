import tempfile
import os

from PIL import Image

from django.test import TestCase

# Create your tests here.
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')

def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])

class PublicRecipeAPI(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_loguin_required(self):
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class TestPrivateRecipeAPI(TestCase):

    def sample_ingredient(self, **params):
        defaults = {
            'user': self.user,
            'name': 'Ingredient test',
        }
        defaults.update(params)
        return Ingredient.objects.create(**defaults)

    def sample_tag(self, **params):
        defaults = {
            'user': self.user,
            'name': 'Tag test',
        }
        defaults.update(params)
        return Tag.objects.create(**defaults)

    def sample_recipe(self, **params):
        defaults = {
            'user': self.user,
            'name': 'Recipe test',
            'price': 300.00,
            'time_minutes': 50
        }
        defaults.update(params)

        return Recipe.objects.create(**defaults)

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@site.com',
            'password123'
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        recipe1 = self.sample_recipe()
        recipe2 = self.sample_recipe()

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_limit_to_user(self):
        anotherUser = get_user_model().objects.create_user("anotherUser@asdmcl.com", "password2")
        recipe1 = self.sample_recipe(user=anotherUser)
        recipe2 = self.sample_recipe()

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data),  1)
        self.assertEqual(res.data[0]['name'], recipe2.name)

    def test_view_recipe_detail(self):
        recipe = self.sample_recipe()
        recipe.tags.add(self.sample_tag())
        recipe.tags.add(self.sample_tag())
        recipe.ingredients.add(self.sample_ingredient())
        recipe.ingredients.add(self.sample_ingredient())
        recipe.ingredients.add(self.sample_ingredient())

        res = self.client.get(detail_url(recipe.id))

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)



    def test_create_recipe_successfull(self):
        payload = {
            'name':'Asado al asador',
            'time_minutes':39,
            'price':300.00
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))


    def test_create_ingredient_invalid(self):
        payload = {'name':''}
        res = self.client.post(RECIPES_URL,payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recipe_with_tags(self):
        tag1 = self.sample_tag()
        tag2 = self.sample_tag()
        payload = {
            'name':'Asado al asador',
            'time_minutes':39,
            'price':300.00,
            'tags':[tag1.id, tag2.id]
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        ingredient1 = self.sample_ingredient()
        ingredient2 = self.sample_ingredient()
        ingredient3 = self.sample_ingredient()
        payload = {
            'name':'Asado al asador',
            'time_minutes':39,
            'price':300.00,
            'ingredients':[ingredient1.id, ingredient2.id]
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)
        self.assertNotIn(ingredient3, ingredients)

class TestRecipeImageUploadAPI(TestCase):
    def sample_recipe(self, **params):
        defaults = {
            'user': self.user,
            'name': 'Recipe test',
            'price': 300.00,
            'time_minutes': 50
        }
        defaults.update(params)

        return Recipe.objects.create(**defaults)

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@site.com',
            '1234'
        )
        self.client.force_authenticate(self.user)
        self.recipe = self.sample_recipe()

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".png") as ntf:
            img = Image.new('RGB',(10,10))
            img.save(ntf, format='PNG')
            ntf.seek(0)
            res = self.client.post(url, {'image':ntf}, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image':'notImage'}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
