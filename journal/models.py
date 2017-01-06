from django.db import models
import uuid


class Journal(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    content = models.BinaryField(editable=True)
    deleted = models.BooleanField(default=False)


class Entry(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    content = models.BinaryField(editable=True)
    journal = models.ForeignKey(Journal)
