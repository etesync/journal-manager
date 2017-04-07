import json
import hashlib

from django.test import TestCase
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

from journal import models, serializers


User = get_user_model()


class BaseTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username='user1')
        self.user2 = User.objects.create(username='user2')
        self.client = APIClient()
        self.raw_client = Client()
        self.random_hash_seed = 1

    def get_random_hash(self):
        """Not really random, generates a sha256 hash that is consistent across runs"""
        ret = hashlib.sha256(bytes(self.random_hash_seed)).hexdigest()
        self.random_hash_seed = self.random_hash_seed + 1
        return ret


class ApiJournalTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.serializer = serializers.JournalSerializer

    def test_only_owner(self):
        """Check all the endpoints correctly require authentication"""
        journal = models.Journal(owner=self.user1, uid=self.get_random_hash(), content=b'test')
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
        response = self.client.get(reverse('journal-detail', kwargs={'uid': journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.user2)
        response = self.client.get(reverse('journal-detail', kwargs={'uid': journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Update
        self.client.force_authenticate(user=self.user1)
        response = self.client.put(reverse('journal-detail', kwargs={'uid': journal.uid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.user2)
        response = self.client.put(reverse('journal-detail', kwargs={'uid': journal.uid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Destroy
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(reverse('journal-detail', kwargs={'uid': journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        ## This actuall destroys the object, so has to be last.
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(reverse('journal-detail', kwargs={'uid': journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Post directly (without it existing)
        journal.uid = self.get_random_hash()
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(reverse('journal-detail', kwargs={'uid': journal.uid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        journal.uid = self.get_random_hash()
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(reverse('journal-detail', kwargs={'uid': journal.uid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_crud_basic(self):
        """Test adding/removing/changing journals"""
        # Not saved
        journal = models.Journal(uid=self.get_random_hash(), content=b'test')
        self.client.force_authenticate(user=self.user1)

        # Add
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get
        response = self.client.get(reverse('journal-detail', kwargs={'uid': journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, self.serializer(journal).data)

        response = self.client.get(reverse('journal-detail', kwargs={'uid': self.get_random_hash()}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Update
        response = self.client.put(reverse('journal-detail', kwargs={'uid': journal.uid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Partial update
        response = self.client.patch(reverse('journal-detail', kwargs={'uid': journal.uid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # List
        response = self.client.get(reverse('journal-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data[0], self.serializer(journal).data)

        # Destroy
        ## This actually destroys the object, so has to be last.
        response = self.client.delete(reverse('journal-detail', kwargs={'uid': journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        ## Verify not returned in api but still in db (both list and get)
        response = self.client.get(reverse('journal-detail', kwargs={'uid': journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(reverse('journal-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        ## And that we can't update it
        journal2 = models.Journal.objects.get(uid=journal.uid)
        journal2.content = b'different'
        response = self.client.put(reverse('journal-detail', kwargs={'uid': journal.uid}), self.serializer(journal2).data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        journal2 = models.Journal.objects.get(uid=journal.uid)
        self.assertEqual(journal.content, journal2.content)

        journal = models.Journal.objects.get(uid=journal.uid)
        self.assertEqual(journal.deleted, True)

        # Put directly (without it existing)
        journal.uid = self.get_random_hash()
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(reverse('journal-detail', kwargs={'uid': journal.uid}), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_errors_basic(self):
        """Test basic validation errors"""
        # Not saved on purpose
        journal = models.Journal(content=b'test')
        self.client.force_authenticate(user=self.user1)

        # Put bad/empty uid
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        journal.uid = "12"
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Put none/empty content
        journal.uid = self.get_random_hash()
        journal.content = b''
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        # FIXME self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        journal.content = None
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        # FIXME self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Put existing uid
        journal.uid = self.get_random_hash()
        journal.content = b'test'
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_read_only(self):
        """Check all read-only objects/methods are really read only"""
        journal = models.Journal(owner=self.user1, uid=self.get_random_hash(), content=b'test')
        journal.save()
        self.client.force_authenticate(user=self.user1)

        # Not allowed to change UID
        journal2 = models.Journal(owner=self.user1, uid=self.get_random_hash(), content=b'test')
        response = self.client.put(reverse('journal-detail', kwargs={'uid': journal.uid}), self.serializer(journal2).data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(journal, models.Journal.objects.get(uid=journal.uid))

        # Not allowed to change version
        journal.version = 137
        response = self.client.put(reverse('journal-detail', kwargs={'uid': journal.uid}), self.serializer(journal2).data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(journal, models.Journal.objects.get(uid=journal.uid))

    def test_version(self):
        """Check version behaves correctly"""
        journal = models.Journal(owner=self.user1, uid=self.get_random_hash(), content=b'test')
        journal.save()
        self.client.force_authenticate(user=self.user1)

        # Default version is 1
        response = self.client.get(reverse('journal-detail', kwargs={'uid': journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Saving version works
        journal = models.Journal(owner=self.user1, uid=self.get_random_hash(), content=b'test', version=12)
        response = self.client.post(reverse('journal-list'), self.serializer(journal).data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(journal.version, models.Journal.objects.get(uid=journal.uid).version)

        # Version readonly is handled in test_read_only
        pass

    def test_filler(self):
        """Extra calls to cheat coverage (things we don't really care about)"""
        str(models.Journal(uid=self.get_random_hash(), content=b'1'))


class ApiEntryTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.serializer = serializers.EntrySerializer

        self.journal = models.Journal(owner=self.user1, uid=self.get_random_hash(), content=b'test')
        self.journal.save()

    def test_only_owner(self):
        """Check all the endpoints correctly require authentication"""
        entry = models.Entry(journal=self.journal, uid=self.get_random_hash(), content=b'test')
        entry.save()

        # List
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        self.client.force_authenticate(user=self.user2)
        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Get
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('entry-detail', kwargs={'uid': entry.uid, 'journal': self.journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.user2)
        response = self.client.get(reverse('entry-detail', kwargs={'uid': entry.uid, 'journal': self.journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Update
        self.client.force_authenticate(user=self.user1)
        response = self.client.put(reverse('entry-detail', kwargs={'journal': self.journal.uid, 'uid': entry.uid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user2)
        response = self.client.put(reverse('entry-detail', kwargs={'journal': self.journal.uid, 'uid': entry.uid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Add to a different user's journal
        entry.uid = self.get_random_hash()
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}) + '?last={}'.format(models.Entry.objects.last().uid), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        entry.uid = self.get_random_hash()
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        ## Try to update an entry a user doesn't own
        entry.uid = self.get_random_hash()
        self.client.force_authenticate(user=self.user2)
        response = self.client.put(reverse('entry-detail', kwargs={'uid': entry.uid, 'journal': self.journal.uid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_crud_basic(self):
        """Test adding/removing/changing entries"""
        # Not saved
        entry = models.Entry(uid=self.get_random_hash(), content=b'test')
        self.client.force_authenticate(user=self.user1)

        # Add
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Add multiple
        multi = [models.Entry(uid=self.get_random_hash(), content=b'test'), models.Entry(uid=self.get_random_hash(), content=b'test'), models.Entry(uid=self.get_random_hash(), content=b'test')]
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}) + '?last={}'.format(models.Entry.objects.last().uid), json.dumps(self.serializer(multi, many=True).data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        ## Verify we got as many we expected
        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        # Get
        response = self.client.get(reverse('entry-detail', kwargs={'uid': entry.uid, 'journal': self.journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, self.serializer(entry).data)

        # Update
        response = self.client.put(reverse('entry-detail', kwargs={'uid': entry.uid, 'journal': self.journal.uid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Partial update
        response = self.client.patch(reverse('entry-detail', kwargs={'uid': entry.uid, 'journal': self.journal.uid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # List
        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data[0], self.serializer(entry).data)

        # Destroy
        ## This actually destroys the object, so has to be last.
        response = self.client.delete(reverse('entry-detail', kwargs={'uid': entry.uid, 'journal': self.journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        ## Verify deletion failed (both in api an db)
        response = self.client.get(reverse('entry-detail', kwargs={'uid': entry.uid, 'journal': self.journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry = models.Entry.objects.get(uid=entry.uid)

        # Put directly (without it existing)
        entry.uid = self.get_random_hash()
        response = self.client.post(reverse('entry-detail', kwargs={'journal': self.journal.uid, 'uid': entry.uid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_errors_basic(self):
        """Test basic validation errors"""
        # Not saved on purpose
        entry = models.Entry(content=b'test')
        self.client.force_authenticate(user=self.user1)

        # Put bad/empty uid
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        entry.uid = "12"
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Put none/empty content
        entry.content = b''
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}), self.serializer(entry).data)
        # FIXME self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        entry.content = None
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}), self.serializer(entry).data)
        # FIXME self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Put existing uid
        entry.uid = self.get_random_hash()
        entry.content = b'test'
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}) + '?last={}'.format(models.Entry.objects.last().uid), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Add multiple with one existing. No update to nothing.
        multi = [models.Entry(uid=self.get_random_hash(), content=b'test'), entry, models.Entry(uid=self.get_random_hash(), content=b'test')]
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}), json.dumps(self.serializer(multi, many=True).data), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        ## Verify we got as many we expected (none)
        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


    def test_read_only(self):
        """Check all read-only objects/methods are really read only"""
        # This object should be read-only anyway, but in case we ever change that, test the harder constraints.
        entry = models.Entry(journal=self.journal, uid=self.get_random_hash(), content=b'test')
        entry.save()
        self.client.force_authenticate(user=self.user1)

        # Not allowed to change UID
        entry2 = models.Entry(journal=self.journal, uid=self.get_random_hash(), content=b'test')
        response = self.client.put(reverse('entry-detail', kwargs={'uid': entry.uid, 'journal': self.journal.uid}), self.serializer(entry2).data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(entry, models.Entry.objects.get(uid=entry.uid))

    def test_fetch_with_last(self):
        """Test using the 'last' query param"""
        # Not saved on purpose
        entry = models.Entry(journal=self.journal, uid=self.get_random_hash(), content=b'1')
        entry.save()
        entry2 = models.Entry(journal=self.journal, uid=self.get_random_hash(), content=b'2')
        entry2.save()
        entry = models.Entry(journal=self.journal, uid=self.get_random_hash(), content=b'3')
        entry.save()
        self.client.force_authenticate(user=self.user1)

        # List
        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uid}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uid}) + '?last={}'.format(response.data[0]['uid']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uid}) + '?last={}'.format(response.data[0]['uid']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        ## Also verify it's really the one we expect to be last
        self.assertEqual(response.data[0]['uid'], entry.uid)

        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uid}) + '?last={}'.format(response.data[0]['uid']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # Non-existent last
        response = self.client.get(reverse('entry-list', kwargs={'journal': self.journal.uid}) + '?last={}'.format(self.get_random_hash()))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Add
        ## With correct last
        entry = models.Entry(journal=self.journal, uid=self.get_random_hash(), content=b'3')
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}) + '?last={}'.format(models.Entry.objects.last().uid), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ## With incorrect last
        entry = models.Entry(journal=self.journal, uid=self.get_random_hash(), content=b'3')
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}) + '?last={}'.format(entry2.uid), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        ## With non-existing last
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}) + '?last={}'.format(self.get_random_hash()), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        ## Missing a last
        response = self.client.post(reverse('entry-list', kwargs={'journal': self.journal.uid}), self.serializer(entry).data)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_filler(self):
        """Extra calls to cheat coverage (things we don't really care about)"""
        str(models.Entry(uid=self.get_random_hash(), content=b'1'))


class DebugOnlyTestCase(BaseTestCase):
    def test_only_debug(self):
        """This endpoint should only be allowed in debug mode"""
        user = User.objects.create(username='test@localhost', email='test@localhost')
        self.raw_client.force_login(user=user)

        response = self.raw_client.post(reverse('reset_debug'), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, b'Only allowed in debug mode.')

    @override_settings(DEBUG=True)
    def test_reset(self):
        """Specifically verify that this endpoint behaves correctly when debug is set"""
        user = User.objects.create(username='test@localhost', email='test@localhost')

        # No user
        response = self.raw_client.post(reverse('reset_debug'), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Disallowed user
        self.raw_client.force_login(user=self.user1)
        response = self.raw_client.post(reverse('reset_debug'), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Allowed user
        self.raw_client.force_login(user=user)
        response = self.raw_client.post(reverse('reset_debug'), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
