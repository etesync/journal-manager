from django.db import models
from django.conf import settings


class Journal(models.Model):
    uuid = models.UUIDField(db_index=True, unique=True, blank=False, null=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.BinaryField(editable=True, blank=False, null=False)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return "Journal<{}>".format(self.uuid)


class Entry(models.Model):
    uuid = models.UUIDField(db_index=True, unique=True, blank=False, null=False)
    content = models.BinaryField(editable=True, blank=False, null=False)
    journal = models.ForeignKey(Journal)

    def __str__(self):
        return "Entry<{}>".format(self.uuid)
