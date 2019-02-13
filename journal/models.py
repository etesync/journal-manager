from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator


Sha256Validator = RegexValidator(regex=r'[a-fA-F0-9]{64}', message='Not a sha256 value.')


class Journal(models.Model):
    uid = models.CharField(db_index=True, blank=False, null=False,
                           max_length=64, validators=[Sha256Validator])
    version = models.PositiveSmallIntegerField(default=1)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.BinaryField(editable=True, blank=False, null=False)
    modified = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('uid', 'owner')

    def __str__(self):
        return "Journal<{}>".format(self.uid)


class Entry(models.Model):
    uid = models.CharField(db_index=True, blank=False, null=False,
                           max_length=64, validators=[Sha256Validator])
    content = models.BinaryField(editable=True, blank=False, null=False)
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('uid', 'journal')
        ordering = ['id']

    def __str__(self):
        return "Entry<{}>".format(self.uid)


class JournalMember(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.BinaryField(editable=True, blank=False, null=False)
    readOnly = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'journal')

    def __str__(self):
        return "JournalMember<{}>".format(self.user)


class UserInfo(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    version = models.PositiveSmallIntegerField(default=1)
    pubkey = models.BinaryField(editable=True, blank=False, null=False)
    content = models.BinaryField(editable=True, blank=False, null=False)

    def __str__(self):
        return "UserInfo<{}>".format(self.owner)
