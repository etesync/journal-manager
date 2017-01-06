import uuid

from django.db import models
from django.conf import settings


class Journal(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.BinaryField(editable=True)
    deleted = models.BooleanField(default=False)


class Entry(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    content = models.BinaryField(editable=True)
    journal = models.ForeignKey(Journal)
