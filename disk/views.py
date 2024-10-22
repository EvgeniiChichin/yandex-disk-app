import os
from django.conf import settings
import zipfile
import requests
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from typing import Any, Dict, List, Optional, Union
from .filter_files_by_type import filter_files_by_type
from .forms import KeyForm


class FileView(View):

    def __init__(self, **kwargs: Any) -> None:
        """Инициализирует класс FileView с настройками API и токеном."""
        super().__init__(**kwargs)
        self.oauth_token = settings.OAUTH_TOKEN
        self.api_url = settings.API_URL
        self.headers = {
            'Authorization': f'OAuth {self.oauth_token}'
        }

    def get(self, request) -> HttpResponse:
        """Обрабатывает GET-запрос и отображает форму для ввода публичного ключа."""
        form = KeyForm()
        return render(request, 'home.html', {'form': form})

    def post(self, request) -> HttpResponse:
        """Обрабатывает POST-запрос для получения данных с Yandex API или для скачивания файлов."""
        form = KeyForm(request.POST)

        if 'download' in request.POST:
            return self.download_multiple_files(request)

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

    def get_files_data(self, public_key: str) -> Union[List[Dict[str, Any]], str]:
        """Получает данные файлов из Yandex Disk API и формирует список."""
        data = cache.get(public_key)

        if data is None:
            params = {'public_key': public_key}
            response = requests.get(
                self.api_url, headers=self.headers, params=params)

            if response.status_code == 200:
                data = response.json()
                cache.set(public_key, data, timeout=3600)

                if 'type' in data and data['type'] == 'file':
                    return [self.process_single_file_data(data, public_key)]

                return self.process_files_data(data, public_key)
            else:
                return f"Ошибка: {response.status_code}"
        else:
            if 'type' in data and data['type'] == 'file':
                return [self.process_single_file_data(data, public_key)]
            return self.process_files_data(data, public_key)

    def process_single_file_data(self, data: Dict[str, Any], public_key: str) -> Dict[str, Any]:
        """Обрабатывает данные одиночного файла и добавляет ссылку на скачивание."""
        file_info = {
            'name': data.get('name'),
            'media_type': data.get('media_type'),
            'mime_type': data.get('mime_type'),
            'size': data.get('size', 0),
            'created': data.get('created'),
            'type': data.get('type'),
            'path': data.get('path')
        }
        if data['type'] == 'file':
            download_url = self.get_download_url(public_key, data['path'])
            if download_url:
                file_info['download_link'] = download_url
            else:
                file_info['download_link'] = None
                print(f"Ошибка получения ссылки на скачивание для {
                      data['name']}")
        return file_info

    def process_files_data(self, data: Dict[str, Any], public_key: str) -> List[Dict[str, Any]]:
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
                    print(f"Ошибка получения ссылки на скачивание для {
                          item['name']}")
            files_data.append(file_info)
        return files_data

    def get_download_url(self, public_key: str, path: str) -> Optional[str]:
        """Формирует URL для скачивания файла."""
        cache_key = f'download_url_{public_key}_{path}'
        download_url = cache.get(cache_key)
        if download_url is None:
            download_url = f"{settings.DOWNLOAD_URL}{
                public_key}&path=%2F{path.lstrip('/')}"
            download_response = requests.get(
                download_url, headers=self.headers)
            if download_response.status_code == 200:
                download_url = download_response.json().get('href')
                cache.set(cache_key, download_url, timeout=3600)
            else:
                return None
        return download_url

    def download_multiple_files(self, request) -> HttpResponse:
        """Скачивание нескольких файлов в виде ZIP-архива."""
        public_key = request.POST.get('public_key')
        file_paths = request.POST.getlist('file_paths')

        if not file_paths or not public_key:
            return HttpResponse("Ошибка: Не указаны файлы или публичный ключ для скачивания.")

        zip_filename = 'downloaded_files.zip'
        zip_file_path = os.path.join('/tmp', zip_filename)

        try:
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for file_path in file_paths:
                    download_url = self.get_download_url(public_key, file_path)
                    if download_url:
                        response = requests.get(download_url)
                        if response.status_code == 200:
                            zipf.writestr(file_path, response.content)
                        else:
                            print(f"Ошибка скачивания файла {
                                  file_path}: {response.status_code}")
                    else:
                        print(f"Ошибка получения URL для файла {file_path}")

            with open(zip_file_path, 'rb') as zipf:
                response = HttpResponse(
                    zipf.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename={
                    zip_filename}'
                return response

        finally:
            if os.path.exists(zip_file_path):
                os.remove(zip_file_path)
