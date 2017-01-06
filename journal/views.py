import uuid

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from .models import Entry, Journal
from .serializers import EntrySerializer


class BaseViewSet(viewsets.ModelViewSet):
    allowed_methods = ['GET', 'PUT']
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)

    def get_user_queryset(self, queryset, user):
        if (self.request.user.is_authenticated()):
            return queryset


class EntryViewSet(BaseViewSet):
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer

    def get_queryset(self):
        queryset =  self.get_user_queryset(type(self).queryset, self.request.user)
        journal = uuid.UUID(self.kwargs['journal'])
        return queryset.filter(journal__uuid=journal)

    def list(self, request, journal):
        last = request.query_params.get('last', None)
        if last is not None:
            queryset = self.get_queryset()

            last_entry = queryset.get(uuid=last)
            queryset = queryset.filter(id__gt=last_entry.id)

            serializer = self.serializer_class(queryset, many=True)
            return Response(serializer.data)

        return super().list(self, request)

    def put(self, request, journal):
        journal = uuid.UUID(journal)
        journal_object = Journal.objects.get(uuid=journal)

        serializer = self.serializer_class(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save(journal=journal_object)
            return Response({}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
