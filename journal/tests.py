import uuid

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import force_authenticate

from . import models, views, serializers


User = get_user_model()


class BaseTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username='user1')
        self.user2 = User.objects.create(username='user2')
        self.client = APIClient()


class ApiJournalTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.serializer = serializers.JournalSerializer

    def test_only_owner(self):
        """Check all the endpoints correctly require authentication"""
        journal = models.Journal(owner=self.user1, uuid=uuid.uuid4(), content=b'test')
        journal.save()

        # List
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('journal-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        self.client.force_authenticate(user=self.user2)
        response = self.client.get(reverse('journal-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(response.data, [])

        # Get
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('journal-detail', kwargs={'uuid': journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.user2)
        response = self.client.get(reverse('journal-detail', kwargs={'uuid': journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Update
        self.client.force_authenticate(user=self.user1)
        response = self.client.put(reverse('journal-detail', kwargs={'uuid': journal.uuid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.user2)
        response = self.client.put(reverse('journal-detail', kwargs={'uuid': journal.uuid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Destroy
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(reverse('journal-detail', kwargs={'uuid': journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        ## This actuall destroys the object, so has to be last.
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(reverse('journal-detail', kwargs={'uuid': journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Post directly (without it existing)
        journal.uuid = uuid.uuid4()
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(reverse('journal-detail', kwargs={'uuid': journal.uuid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        journal.uuid = uuid.uuid4()
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(reverse('journal-detail', kwargs={'uuid': journal.uuid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_crud_basic(self):
        """Test adding/removing/changing journals"""
        # Not saved
        journal = models.Journal(uuid=uuid.uuid4(), content=b'test')
        self.client.force_authenticate(user=self.user1)

        # Add
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get
        response = self.client.get(reverse('journal-detail', kwargs={'uuid': journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, self.serializer(journal).data)

        # Update
        response = self.client.put(reverse('journal-detail', kwargs={'uuid': journal.uuid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Partial update
        response = self.client.patch(reverse('journal-detail', kwargs={'uuid': journal.uuid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # List
        response = self.client.get(reverse('journal-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data[0], self.serializer(journal).data)

        # Destroy
        ## This actually destroys the object, so has to be last.
        response = self.client.delete(reverse('journal-detail', kwargs={'uuid': journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        ## Verify not returned in api but still in db (both list and get)
        response = self.client.get(reverse('journal-detail', kwargs={'uuid': journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(reverse('journal-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        ## And that we can't update it
        journal2 = models.Journal.objects.get(uuid=journal.uuid)
        journal2.content = b'different'
        response = self.client.put(reverse('journal-detail', kwargs={'uuid': journal.uuid}), self.serializer(journal2).data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        journal2 = models.Journal.objects.get(uuid=journal.uuid)
        self.assertEqual(journal.content, journal2.content)

        journal = models.Journal.objects.get(uuid=journal.uuid)
        self.assertEqual(journal.deleted, True)

        # Put directly (without it existing)
        journal.uuid = uuid.uuid4()
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(reverse('journal-detail', kwargs={'uuid': journal.uuid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_errors_basic(self):
        """Test basic validation errors"""
        # Not saved on purpose
        journal = models.Journal(content=b'test')
        self.client.force_authenticate(user=self.user1)

        # Put bad/empty uuid
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        journal.uuid = "12"
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Put none/empty content
        journal.uuid = uuid.uuid4()
        journal.content = b''
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        # FIXME self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        journal.content = None
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        # FIXME self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Put existing uuid
        journal.uuid = uuid.uuid4()
        journal.content = b'test'
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_read_only(self):
        """Check all read-only objects/methods are really read only"""
        journal = models.Journal(owner=self.user1, uuid=uuid.uuid4(), content=b'test')
        journal.save()
        self.client.force_authenticate(user=self.user1)

        # Not allowed to change UUID
        journal2 = models.Journal(owner=self.user1, uuid=uuid.uuid4(), content=b'test')
        response = self.client.put(reverse('journal-detail', kwargs={'uuid': journal.uuid}), self.serializer(journal2).data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(journal, models.Journal.objects.get(uuid=journal.uuid))


class ApiEntryTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.serializer = serializers.EntrySerializer

        self.journal = models.Journal(owner=self.user1, uuid=uuid.uuid4(), content=b'test')
        self.journal.save()

    def test_only_owner(self):
        """Check all the endpoints correctly require authentication"""
        entry = models.Entry(journal=self.journal, uuid=uuid.uuid4(), content=b'test')
        entry.save()

        # List
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        self.client.force_authenticate(user=self.user2)
        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(response.data, [])

        # Get
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('entry-detail', kwargs={'uuid': entry.uuid, 'journal': self.journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.user2)
        response = self.client.get(reverse('entry-detail', kwargs={'uuid': entry.uuid, 'journal': self.journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Update
        self.client.force_authenticate(user=self.user1)
        response = self.client.put(reverse('entry-detail', kwargs={'journal': self.journal.uuid, 'uuid': entry.uuid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user2)
        response = self.client.put(reverse('entry-detail', kwargs={'journal': self.journal.uuid, 'uuid': entry.uuid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Add to a different user's journal
        entry.uuid = uuid.uuid4()
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uuid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        entry.uuid = uuid.uuid4()
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uuid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        ## Try to update an entry a user doesn't own
        entry.uuid = uuid.uuid4()
        self.client.force_authenticate(user=self.user2)
        response = self.client.put(reverse('entry-detail', kwargs={'uuid': entry.uuid, 'journal': self.journal.uuid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_crud_basic(self):
        """Test adding/removing/changing entries"""
        # Not saved
        entry = models.Entry(uuid=uuid.uuid4(), content=b'test')
        self.client.force_authenticate(user=self.user1)

        # Add
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uuid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get
        response = self.client.get(reverse('entry-detail', kwargs={'uuid': entry.uuid, 'journal': self.journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, self.serializer(entry).data)

        # Update
        response = self.client.put(reverse('entry-detail', kwargs={'uuid': entry.uuid, 'journal': self.journal.uuid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Partial update
        response = self.client.patch(reverse('entry-detail', kwargs={'uuid': entry.uuid, 'journal': self.journal.uuid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # List
        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data[0], self.serializer(entry).data)

        # Destroy
        ## This actually destroys the object, so has to be last.
        response = self.client.delete(reverse('entry-detail', kwargs={'uuid': entry.uuid, 'journal': self.journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        ## Verify deletion failed (both in api an db)
        response = self.client.get(reverse('entry-detail', kwargs={'uuid': entry.uuid, 'journal': self.journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry = models.Entry.objects.get(uuid=entry.uuid)

        # Put directly (without it existing)
        entry.uuid = uuid.uuid4()
        response = self.client.post(reverse('entry-detail', kwargs={'journal': self.journal.uuid, 'uuid': entry.uuid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_errors_basic(self):
        """Test basic validation errors"""
        # Not saved on purpose
        entry = models.Entry(content=b'test')
        self.client.force_authenticate(user=self.user1)

        # Put bad/empty uuid
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uuid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        entry.uuid = "12"
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uuid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Put none/empty content
        entry.content = b''
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uuid}), self.serializer(entry).data)
        # FIXME self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        entry.content = None
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uuid}), self.serializer(entry).data)
        # FIXME self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Put existing uuid
        entry.uuid = uuid.uuid4()
        entry.content = b'test'
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uuid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uuid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_read_only(self):
        """Check all read-only objects/methods are really read only"""
        # This object should be read-only anyway, but in case we ever change that, test the harder constraints.
        entry = models.Entry(journal=self.journal, uuid=uuid.uuid4(), content=b'test')
        entry.save()
        self.client.force_authenticate(user=self.user1)

        # Not allowed to change UUID
        entry2 = models.Entry(journal=self.journal, uuid=uuid.uuid4(), content=b'test')
        response = self.client.put(reverse('entry-detail', kwargs={'uuid': entry.uuid, 'journal': self.journal.uuid}), self.serializer(entry2).data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(entry, models.Entry.objects.get(uuid=entry.uuid))

    def test_fetch_with_last(self):
        """Test using the 'last' query param"""
        # Not saved on purpose
        entry = models.Entry(journal=self.journal, uuid=uuid.uuid4(), content=b'1')
        entry.save()
        entry = models.Entry(journal=self.journal, uuid=uuid.uuid4(), content=b'2')
        entry.save()
        entry = models.Entry(journal=self.journal, uuid=uuid.uuid4(), content=b'3')
        entry.save()
        self.client.force_authenticate(user=self.user1)

        # List
        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uuid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uuid}) + '?last={}'.format(response.data[0]['uuid']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uuid}) + '?last={}'.format(response.data[0]['uuid']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        ## Also verify it's really the one we expect to be last
        self.assertEqual(uuid.UUID(response.data[0]['uuid']), entry.uuid)

        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uuid}) + '?last={}'.format(response.data[0]['uuid']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # Non-existent last
        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uuid}) + '?last={}'.format(uuid.uuid4()))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
