from django.conf import settings
from django.contrib.auth import login
from django.db import IntegrityError, transaction
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from . import app_settings
from .models import Entry, Journal
from .serializers import EntrySerializer, JournalSerializer, JournalUpdateSerializer


class BaseViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = app_settings.API_PERMISSIONS

    def get_serializer_class(self):
        serializer_class = self.serializer_class

        if self.request.method == 'PUT':
            serializer_class = getattr(self, 'serializer_update_class', serializer_class)

        return serializer_class


class JournalViewSet(BaseViewSet):
    allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
    queryset = Journal.objects.all()
    serializer_class = JournalSerializer
    serializer_update_class = JournalUpdateSerializer
    lookup_field = 'uid'

    def get_queryset(self):
        queryset = type(self).queryset
        return queryset.filter(owner=self.request.user, deleted=False)

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


class EntryViewSet(BaseViewSet):
    allowed_methods = ['GET', 'POST']
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    lookup_field = 'uid'

    def get_queryset(self):
        journal_uid = self.kwargs['journal']
        journal = get_object_or_404(Journal, owner=self.request.user, uid=journal_uid)
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
        last = request.query_params.get('last', None)
        if last is not None:
            queryset = self.get_queryset()

            last_entry = get_object_or_404(queryset, uid=last)
            last_in_db = queryset.last()
            if last_entry != last_in_db:
                return Response({}, status=status.HTTP_409_CONFLICT)

        journal_object = get_object_or_404(Journal, owner=self.request.user, uid=journal)

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


@csrf_exempt
@require_POST
def reset(request):
    # Only run when in DEBUG mode! It's only used for tests
    if not settings.DEBUG:
        return HttpResponseBadRequest("Only allowed in debug mode.")

    user, token = TokenAuthentication().authenticate(request)

    login(request, user)

    # Hardcoded user, for extra safety
    if request.user.email != 'test@localhost':
        return HttpResponseBadRequest("Endpoint not allowed for user.")

    # Delete all of the journal data for this user for a clear test env
    request.user.journal_set.all().delete()

    return HttpResponse()
