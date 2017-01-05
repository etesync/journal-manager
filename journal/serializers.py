from rest_framework import serializers
from . import models

class EntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Entry
        fields = ('uuid', 'content')
