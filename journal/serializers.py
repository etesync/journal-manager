import base64

from django.contrib.auth import get_user_model
from rest_framework import serializers
from . import models

User = get_user_model()


class BinaryBase64Field(serializers.Field):
    def to_representation(self, value):
        return base64.b64encode(value).decode('ascii')

    def to_internal_value(self, data):
        return base64.b64decode(data)


class JournalSerializer(serializers.ModelSerializer):
    content = BinaryBase64Field()
    owner = serializers.SlugRelatedField(
        slug_field=User.USERNAME_FIELD,
        read_only=True
    )
    key = serializers.SerializerMethodField('get_key_from_context')
    readOnly = serializers.SerializerMethodField('get_read_only_from_context')
    lastUid = serializers.SerializerMethodField('get_last_uid')

    class Meta:
        model = models.Journal
        fields = ('version', 'uid', 'content', 'owner', 'key', 'readOnly', 'lastUid')

    def get_key_from_context(self, obj):
        request = self.context.get('request', None)
        if request is not None:
            try:
                member = obj.members.get(user=request.user)
                serialized_member = JournalMemberSerializer(member)
                return serialized_member.data['key']
            except models.JournalMember.DoesNotExist:
                pass
        return None

    def get_read_only_from_context(self, obj):
        request = self.context.get('request', None)
        if request is not None:
            try:
                member = obj.members.get(user=request.user)
                return member.readOnly
            except models.JournalMember.DoesNotExist:
                pass
        return False

    def get_last_uid(self, obj):
        last = obj.entry_set.last()
        if last:
            return last.uid
        return None


class JournalUpdateSerializer(JournalSerializer):
    class Meta(JournalSerializer.Meta):
        fields = ('content', )


class EntrySerializer(serializers.ModelSerializer):
    content = BinaryBase64Field()

    class Meta:
        model = models.Entry
        fields = ('uid', 'content')


class UserInfoSerializer(serializers.ModelSerializer):
    content = BinaryBase64Field()
    pubkey = BinaryBase64Field()

    class Meta:
        model = models.UserInfo
        fields = ('version', 'pubkey', 'content')


class UserInfoPublicSerializer(UserInfoSerializer):
    class Meta(JournalSerializer.Meta):
        fields = ('version', 'pubkey')


class JournalMemberSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field=User.USERNAME_FIELD,
        queryset=User.objects
    )
    key = BinaryBase64Field()

    class Meta:
        model = models.JournalMember
        fields = ('user', 'key', 'readOnly')
