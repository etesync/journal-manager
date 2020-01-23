from django.conf import settings
from django.contrib.auth import login, get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseBadRequest, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response

from . import app_settings, permissions, paginators
from .models import Entry, Journal, UserInfo, JournalMember
from .serializers import (
        EntrySerializer, JournalSerializer, JournalUpdateSerializer,
        UserInfoSerializer, UserInfoPublicSerializer,
        JournalMemberSerializer
    )


User = get_user_model()


class BaseViewSet(viewsets.ModelViewSet):
    authentication_classes = tuple(app_settings.API_AUTHENTICATORS)
    permission_classes = tuple(app_settings.API_PERMISSIONS)

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.request.method == 'PUT':
            serializer_class = getattr(self, 'serializer_update_class', serializer_class)

        return serializer_class

    def get_journal_queryset(self, queryset=Journal.objects):
        user = self.request.user
        return queryset.filter(Q(owner=user) | Q(members__user=user),
                               deleted=False).distinct()


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

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save(owner=self.request.user)
            except IntegrityError:
                content = {'code': 'integrity_error'}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

            return Response({}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        queryset = self.get_queryset()

        serializer = self.serializer_class(queryset, context={'request': request}, many=True)
        return Response(serializer.data)


class MembersViewSet(BaseViewSet):
    allowed_methods = ['GET', 'POST', 'DELETE']
    permission_classes = BaseViewSet.permission_classes + (permissions.IsJournalOwner, )
    lookup_value_regex = '[^/]+'
    queryset = JournalMember.objects.all()
    serializer_class = JournalMemberSerializer
    lookup_field = 'user__' + User.USERNAME_FIELD
    lookup_url_kwarg = 'username'

    def get_queryset(self):
        journal_uid = self.kwargs['journal_uid']
        return type(self).queryset.filter(journal__uid=journal_uid)

    def create(self, request, journal_uid=None):
        serializer = self.serializer_class(data=request.data)
        journal = get_object_or_404(self.get_journal_queryset(Journal.objects), uid=journal_uid)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save(journal=journal)
            except IntegrityError:
                content = {'code': 'already_exists', 'detail': 'Member arleady exists'}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

            return Response({}, status=status.HTTP_201_CREATED)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, journal_uid=None):
        journal = get_object_or_404(self.get_journal_queryset(Journal.objects), uid=journal_uid)
        members = JournalMember.objects.filter(journal=journal).exclude(user=self.request.user)

        serializer = JournalMemberSerializer(members, many=True)
        return Response(serializer.data)

    def update(self, request, partial, username=None, journal_uid=None):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class EntryViewSet(BaseViewSet):
    allowed_methods = ['GET', 'POST']
    permission_classes = BaseViewSet.permission_classes + (permissions.IsMemberReadOnly, )
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    pagination_class = paginators.LinkHeaderPagination
    lookup_field = 'uid'

    def get_queryset(self, use_last=True):
        journal_uid = self.kwargs['journal_uid']
        try:
            journal = self.get_journal_queryset(Journal.objects).get(uid=journal_uid)
        except Journal.DoesNotExist:
            raise Http404("Journal does not exist")
        queryset = type(self).queryset.filter(journal__pk=journal.pk)

        last = self.request.query_params.get('last', None)
        if use_last and last is not None:
            last_entry = get_object_or_404(queryset, uid=last)
            queryset = queryset.filter(id__gt=last_entry.id)

        return queryset

    def create(self, request, journal_uid=None):
        queryset = self.get_queryset(use_last=False)

        last = request.query_params.get('last', None)
        last_entry = None
        if last is not None:
            last_entry = get_object_or_404(queryset, uid=last)

        journal_object = self.get_journal_queryset(Journal.objects).get(uid=journal_uid)

        many = isinstance(request.data, list)
        serializer = self.serializer_class(data=request.data, many=many)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # We use select_for_update in the next line as to get a lock on the insert.
                    # After the lock is freed we get the up to date last
                    queryset.select_for_update().last()
                    last_in_db = queryset.last()
                    if last_entry != last_in_db:
                        return Response({}, status=status.HTTP_409_CONFLICT)

                    serializer.save(journal=journal_object)
            except IntegrityError:
                content = {'code': 'integrity_error'}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

            return Response({}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, journal_uid=None, uid=None):
        # FIXME: This shouldn't be needed. Doesn't work without for some reason.
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, journal_uid=None, uid=None):
        self.get_object()
        return Response(status=status.HTTP_403_FORBIDDEN)

    def partial_update(self, request, journal_uid=None, uid=None):
        self.get_object()
        return Response(status=status.HTTP_403_FORBIDDEN)


class UserInfoViewSet(BaseViewSet):
    lookup_value_regex = '[^/]+'
    permission_classes = BaseViewSet.permission_classes + (permissions.IsOwnerOrReadOnly, )
    allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
    queryset = UserInfo.objects.all()
    serializer_class = UserInfoSerializer
    lookup_field = 'owner__' + User.USERNAME_FIELD
    lookup_url_kwarg = 'username'

    def get_serializer_class(self):
        # Owners get to see more
        if self.kwargs.get(self.lookup_url_kwarg, '').lower() == \
                getattr(self.request.user, User.USERNAME_FIELD).lower():
            serializer_class = super().get_serializer_class()
        else:
            serializer_class = UserInfoPublicSerializer

        return serializer_class

    def get_object(self):
        username = self.kwargs[self.lookup_url_kwarg]
        queryset = self.get_queryset()
        params = {self.lookup_field + '__iexact': username}
        obj = get_object_or_404(queryset, **params)
        self.check_object_permissions(self.request, obj)
        return obj

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save(owner=self.request.user)
            except IntegrityError:
                content = {'code': 'integrity_error', 'detail': 'Error creating user info.'}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

            return Response({}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # List is not allowed
    def list(self, request):
        return Response(status=status.HTTP_403_FORBIDDEN)


class ResetViewSet(BaseViewSet):
    allowed_methods = ['POST']

    def post(self, request, *args, **kwargs):
        # Only run when in DEBUG mode! It's only used for tests
        if not settings.DEBUG:
            return HttpResponseBadRequest("Only allowed in debug mode.")

        # Only allow local users, for extra safety
        if not request.user.email.endswith('@localhost'):
            return HttpResponseBadRequest("Endpoint not allowed for user.")

        # Delete all of the journal data for this user for a clear test env
        request.user.journal_set.all().delete()
        request.user.journalmember_set.all().delete()
        try:
            request.user.userinfo.delete()
        except ObjectDoesNotExist:
            pass

        return HttpResponse()


reset = ResetViewSet.as_view({'post': 'post'})
