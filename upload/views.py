import os.path as osp
from django.shortcuts import render
# views.py in upload app
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .appfunc import load_yaml, get_token, do_POST  # import the logic from appserver.py

def upload_page(request):
    return render(request, 'upload/upload.html')

@method_decorator(csrf_exempt, name='dispatch')
class AppServerView(View):
    def get(self, request, *args, **kwargs):
        config_path = osp.join(osp.dirname(osp.abspath(__file__)), 'config.yaml')
        token = get_token(load_yaml(config_path))
        # print(token)
        return HttpResponse(token, content_type='text/html; charset=UTF-8',
                            headers={'Access-Control-Allow-Methods':'POST',
                                    'Access-Control-Allow-Origin':'*'})

    def post(self, request, *args, **kwargs):
        response = do_POST(request)  # Modify do_POST to accept a Django request object
        return JsonResponse({'Status': 'OK'}) if response else HttpResponse(status=400)

# You might want to move the logic functions from appserver.py into a separate file like appserver_logic.py

# Create your views here.
