import json

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.http import JsonResponse

from .models import Entry
from .serializers import EntrySerializer


@method_decorator(csrf_exempt, name='dispatch')
class RestView(View):
    def get(self, request):
        last = request.GET.get('last', None)
        if last is None:
            entries = Entry.objects.all()
        else:
            last_entry = Entry.objects.get(uuid=last)
            entries = Entry.objects.filter(id__gt=last_entry.id)

        serializer = EntrySerializer(entries, many=True)
        return JsonResponse({'entries': serializer.data})

    @csrf_exempt
    def put(self, request):
        body = json.loads(request.body.decode())
        entries = EntrySerializer(data=body)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)

        return JsonResponse(serializer.errors, status=400)
