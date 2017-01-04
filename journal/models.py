from django.db import models
import uuid

class Entry(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    content = models.BinaryField()
