import requests

# Твой OAuth-токен
oauth_token = 'y0_AgAAAAAMK9ibAADLWwAAAAEVRnblAABn78_KKJVIVJgAvtCYgPH4WaLHpA'

# URL для запроса к API Яндекс.Диска (публичные ресурсы)
url = 'https://cloud-api.yandex.net/v1/disk/public/resources'

# Параметры запроса
params = {
    'public_key': 'https://disk.yandex.ru/i/cvLx3c8_WtHd7A'  # публичная ссылка на файл
}

# Заголовки с авторизацией
headers = {
    'Authorization': f'OAuth {oauth_token}'
}

# Отправляем GET-запрос с токеном и параметрами
response = requests.get(url, headers=headers, params=params)

# Проверяем статус ответа и выводим результат
if response.status_code == 200:
    data = response.json()  # Преобразуем ответ в JSON
    print('Данные с Яндекс.Диска:', data)
else:
    print(f'Ошибка: {response.status_code}', response.text)