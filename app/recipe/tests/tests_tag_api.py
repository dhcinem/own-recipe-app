from django.test import TestCase

# Create your tests here.
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

class PublicTagsAPI(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_loguin_required(self):
        res = self.client.get(TAGS_URL)

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
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Dessert")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_limited_to_user(self):
        anotherUser = get_user_model().objects.create_user(
            'testAnother@site.com',
            '2password123'
        )
        Tag.objects.create(user=anotherUser, name="Canelones")
        tag = Tag.objects.create(user=self.user, name="Asado")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)


    def test_create_tag_successfull(self):
        payload = {'name':'Test tag'}
        self.client.post(TAGS_URL, payload)

        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        payload = {'name':''}
        res = self.client.post(TAGS_URL,payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
