from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
import requests
from .forms import KeyForm
from django.core.cache import cache
from .filter_files_by_type import filter_files_by_type

class FileView(View):
    oauth_token = ''
    api_url = 'https://cloud-api.yandex.net/v1/disk/public/resources'
    
    headers = {
        'Authorization': f'OAuth {oauth_token}'
    }

    def get(self, request):
        """Обрабатывает GET-запрос и отображает форму для ввода публичного ключа."""
        form = KeyForm()
        return render(request, 'home.html', {'form': form})

    def post(self, request):
        """Обрабатывает POST-запрос и запрашивает данные с Yandex API."""
        form = KeyForm(request.POST)
        if form.is_valid():
            public_key = form.cleaned_data['public_key']
            file_type = form.cleaned_data['file_type']
            files_data = self.get_files_data(public_key)

            if isinstance(files_data, list):
                filtered_files = filter_files_by_type(files_data, file_type)
                return render(request, 'home.html', {'files': filtered_files, 'form': form})
            else:
                return HttpResponse(f"Ошибка: {files_data}")
        return render(request, 'home.html', {'form': form})

    def get_files_data(self, public_key):
        """Получает данные файлов из Yandex Disk API и формирует список."""
        data  = cache.get(public_key)

        if data is None:

            params = {'public_key': public_key}
            response = requests.get(self.api_url, headers=self.headers, params=params)

            if response.status_code == 200:
               data = response.json()
               cache.set(public_key,data,timeout=3600)
               return self.process_files_data(data, public_key)
            else:
               return f"Ошибка: {response.status_code}"
        else:
            return self.process_files_data(data,public_key)

    def process_files_data(self, data, public_key):
        """Обрабатывает данные о файлах и добавляет ссылки на скачивание."""
        files_data = []
        items = data.get('_embedded', {}).get('items', [])
        for item in items:
            file_info = {
                'name': item.get('name'),
                'media_type': item.get('media_type'),
                'mime_type': item.get('mime_type'),
                'size': item.get('size', 0),
                'created': item.get('created'),
                'type': item.get('type'),
                'path': item.get('path')
            }
            if item['type'] == 'file':
                download_url = self.get_download_url(public_key, item['path'])
                if download_url:
                    file_info['download_link'] = download_url
                else:
                    file_info['download_link'] = None
                    print(f"Ошибка получения ссылки на скачивание для {item['name']}")
            files_data.append(file_info)
        return files_data

    def get_download_url(self, public_key, path):
        """Формирует URL для скачивания файла."""
        cache_key = f'download_url_{public_key}_{path}'
        download_url = cache.get(cache_key)
        if download_url is None:
            download_url = f"https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={public_key}&path=%2F{path.lstrip('/')}"
            download_response = requests.get(download_url, headers=self.headers)
            if download_response.status_code == 200:
                download_url = download_response.json().get('href')
                cache.set(cache_key, download_url, timeout=3600)
            else:
                return None
        return download_url
