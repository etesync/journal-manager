import json

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.http import JsonResponse

from .models import Entry


@method_decorator(csrf_exempt, name='dispatch')
class RestView(View):
    def get(self, request):
        last = request.GET.get('last', None)
        if last is None:
            entries = Entry.objects.all()
        else:
            entries = Entry.objects.filter(id__gt=last)

        ret = map(lambda x: {'id': x.id, 'content': x.content.decode()},
                            entries)
        return JsonResponse({'entries': list(ret)})

    @csrf_exempt
    def put(self, request):
        entries = json.loads(request.body.decode())
        for entry in entries['entries']:
            Entry(content=entry['content'].encode()).save()

        res = JsonResponse({'ok': 1})
        res.status_code = 201
        return res
