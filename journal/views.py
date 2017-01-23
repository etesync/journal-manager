from django.db import IntegrityError, transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from .models import Entry, Journal
from .serializers import EntrySerializer, JournalSerializer, JournalUpdateSerializer


class BaseViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)

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
        journal = self.kwargs['journal']
        return type(self).queryset.filter(journal__owner=self.request.user,
                                          journal__uid=journal)

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
