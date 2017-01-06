from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.http import JsonResponse

from rest_framework.parsers import JSONParser

from .models import Entry
from .serializers import EntrySerializer


@method_decorator(csrf_exempt, name='dispatch')
class RestView(View):
    def get(self, request, journal):
        last = request.GET.get('last', None)
        tag = journal
        entries = Entry.objects.filter(tag=tag)
        if last is not None:
            last_entry = entries.get(uuid=last)
            entries = entries.filter(id__gt=last_entry.id)

        serializer = EntrySerializer(entries, many=True)
        return JsonResponse({'entries': serializer.data})

    @csrf_exempt
    def put(self, request, journal):
        tag = journal
        body = JSONParser().parse(request)
        serializer = EntrySerializer(data=body['entries'], many=True)
        if serializer.is_valid():
            serializer.save(tag=tag)
            return JsonResponse({}, status=201)

        return JsonResponse(serializer.errors, status=400)
