from django.db import models


class Entry(models.Model):
    content = models.BinaryField()
