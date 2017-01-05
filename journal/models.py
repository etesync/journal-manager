from django.db import models
import uuid

class Entry(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    content = models.BinaryField(editable=True)
    tag = models.CharField(max_length=200)
