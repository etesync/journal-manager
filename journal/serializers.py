import base64

from django.contrib.auth import get_user_model
from rest_framework import serializers
from . import models

User = get_user_model()


class BinaryBase64Field(serializers.Field):
    def to_representation(self, content):
        return base64.b64encode(content).decode('ascii')

    def to_internal_value(self, data):
        return base64.b64decode(data)


class JournalSerializer(serializers.ModelSerializer):
    content = BinaryBase64Field()
    owner = serializers.SlugRelatedField(
        slug_field=User.USERNAME_FIELD,
        read_only=True
    )
    key = serializers.SerializerMethodField('get_key_from_context')

    class Meta:
        model = models.Journal
        fields = ('version', 'uid', 'content', 'owner', 'key')

    def get_key_from_context(self, obj):
        request = self.context.get('request', None)
        if request is not None:
            try:
                member = obj.members.get(user=request.user)
                serialized_member = JournalMemberSerializer(member)
                return serialized_member.data['key']
            except models.JournalMember.DoesNotExist:
                pass


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
        fields = ('user', 'key')
