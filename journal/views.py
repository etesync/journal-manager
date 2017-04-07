from django.conf import settings
from django.contrib.auth import login, get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import detail_route

from . import app_settings, permissions
from .models import Entry, Journal, UserInfo, JournalMember
from .serializers import (
        EntrySerializer, JournalSerializer, JournalUpdateSerializer,
        UserInfoSerializer, UserInfoPublicSerializer,
        JournalMemberSerializer
    )


User = get_user_model()


class BaseViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = tuple(app_settings.API_PERMISSIONS)

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.request.method == 'PUT':
            serializer_class = getattr(self, 'serializer_update_class', serializer_class)

        return serializer_class

    def get_journal_queryset(self, queryset):
        user = self.request.user
        return queryset.filter(Q(owner=user) | Q(members__user=user),
                               deleted=False)


class JournalViewSet(BaseViewSet):
    allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
    permission_classes = BaseViewSet.permission_classes + (permissions.IsOwnerOrReadOnly, )
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer
    serializer_update_class = JournalUpdateSerializer
    lookup_field = 'uid'

    def get_queryset(self):
        queryset = type(self).queryset
        return self.get_journal_queryset(queryset)

    def destroy(self, request, uid=None):
        journal = self.get_object()
        journal.deleted = True
        journal.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save(owner=self.request.user)
            except IntegrityError:
                content = {'error': 'IntegrityError'}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

            return Response({}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        queryset = self.get_queryset()

        serializer = self.serializer_class(queryset, context={'request': request}, many=True)
        return Response(serializer.data)

    # FIXME: Change into a nested resource
    @detail_route(methods=('GET', 'POST', 'DELETE'))
    def members(self, request, uid=None):
        journal = self.get_object()
        if journal.owner != self.request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if self.request.method == 'GET':
            members = JournalMember.objects.filter(journal=journal)

            serializer = JournalMemberSerializer(members, many=True)
            return Response(serializer.data)
        elif self.request.method == 'POST':
            serializer = JournalMemberSerializer(data=request.data)
            if serializer.is_valid():
                try:
                    with transaction.atomic():
                        serializer.save(journal=journal)
                except IntegrityError:
                    content = {'error': 'IntegrityError'}
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)

                return Response({}, status=status.HTTP_201_CREATED)
        elif self.request.method == 'DELETE':
            serializer = JournalMemberSerializer(data=request.data)
            if serializer.is_valid():
                member = get_object_or_404(JournalMember, user__email=serializer.data['user'], journal=journal)
                member.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)


class EntryViewSet(BaseViewSet):
    allowed_methods = ['GET', 'POST']
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    lookup_field = 'uid'

    def get_queryset(self):
        journal_uid = self.kwargs['journal']
        try:
            journal = self.get_journal_queryset(Journal.objects).get(uid=journal_uid)
        except Journal.DoesNotExist:
            raise Http404("Journal does not exist")
        return type(self).queryset.filter(journal__pk=journal.pk)

    def list(self, request, journal):
        last = request.query_params.get('last', None)
        if last is not None:
            queryset = self.get_queryset()

            last_entry = get_object_or_404(queryset, uid=last)
            queryset = queryset.filter(id__gt=last_entry.id)

            serializer = self.serializer_class(queryset, many=True)
            return Response(serializer.data)

        return super().list(self, request)

    def create(self, request, journal):
        queryset = self.get_queryset()
        last_in_db = queryset.last()

        last = request.query_params.get('last', None)
        last_entry = None
        if last is not None:
            last_entry = get_object_or_404(queryset, uid=last)

        if last_entry != last_in_db:
            return Response({}, status=status.HTTP_409_CONFLICT)

        journal_object = self.get_journal_queryset(Journal.objects).get(uid=journal)

        many = isinstance(request.data, list)
        serializer = self.serializer_class(data=request.data, many=many)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save(journal=journal_object)
            except IntegrityError:
                content = {'error': 'IntegrityError'}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

            return Response({}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, journal, uid=None):
        # FIXME: This shouldn't be needed. Doesn't work without for some reason.
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, journal, uid=None):
        self.get_object()
        return Response(status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, journal, uid=None):
        self.get_object()
        return Response(status=status.HTTP_403_FORBIDDEN)


class UserInfoViewSet(BaseViewSet):
    lookup_value_regex = '[^/]+'
    permission_classes = BaseViewSet.permission_classes + (permissions.IsOwnerOrReadOnly, )
    allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
    queryset = UserInfo.objects.all()
    serializer_class = UserInfoSerializer
    lookup_field = 'owner__email'

    def get_serializer_class(self):
        # Owners get to see more
        if self.kwargs[self.lookup_field] == self.request.user.email:
            serializer_class = super().get_serializer_class()
        else:
            serializer_class = UserInfoPublicSerializer

        return serializer_class

    def get_queryset(self):
        queryset = type(self).queryset
        return queryset

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save(owner=self.request.user)
            except IntegrityError:
                content = {'error': 'IntegrityError'}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

            return Response({}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # List is not allowed
    def list(self, request):
        return Response(status=status.HTTP_403_FORBIDDEN)


@csrf_exempt
@require_POST
def reset(request):
    # Only run when in DEBUG mode! It's only used for tests
    if not settings.DEBUG:
        return HttpResponseBadRequest("Only allowed in debug mode.")

    if not request.user.is_authenticated():
        ret = TokenAuthentication().authenticate(request)

        if ret is None:
            return HttpResponseBadRequest("Couldn't authenticate")

        login(request, ret[0])

    # Hardcoded user, for extra safety
    if request.user.email != 'test@localhost':
        return HttpResponseBadRequest("Endpoint not allowed for user.")

    # Delete all of the journal data for this user for a clear test env
    request.user.journal_set.all().delete()

    return HttpResponse()
