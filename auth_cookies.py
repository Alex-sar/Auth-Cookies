import os
import json
import requests
from pathlib import Path
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from requests.utils import dict_from_cookiejar
from urllib3.util.retry import Retry


class AuthCookies:
    def __init__(self):
        self.auth_url = <'url адрес страницы аутентификации'>
        self.user_web = <'пользователь'>
        self.password_web = <'пароль'>
        self.proxy_url = <"словарь{‘http’: ‘foo.bar:3128’, ‘http://host.name’: ‘foo.bar:4012’}, если proxy_url нет - ''">
        self.directory = <"адрес директории для хранения cookies">
        self.filename = <'название файла с cookies'>
        self.max_retries = <'число повторныз попыток авторизации'>
        # задежка между повторными подключениями
        self.retry_delay = 1
        self.pasport = None

    def save_cookies(self, session):
        # Сохраняет cookies сессии в файл.
        print(f"Создаем директорию {self.directory} и записываем файл {self.filename}")
        Path(self.directory).mkdir(parents= True, exist_ok= True)
        # Сохраняем полученный файл pasport в директории
        self.pasport = dict_from_cookiejar(session.cookies)
        with open(Path(self.directory) / f'{self.filename}.json', 'w+', encoding= 'utf-8') as fd:
            json.dump(self.pasport, fd)
            print(f"Cookie-файл записан в директории {self.directory}")
        return True
    
    def load_cookies(self):
        # Загружает cookies из файла в сессию, если он существует.
        try:
            with open(Path(self.directory) / f'{self.filename}.json', 'r', encoding= 'utf-8') as fd:
                cookies = json.load(fd)
                return cookies
        except FileNotFoundError:
            # Если файл не найден проводим аутентификацию и получаем cookies
            with requests.Session() as session:
                session.get(
                    url= self.auth_url,
                    auth= HTTPBasicAuth(username= self.user_web, password= self.password_web),
                    timeout= 5,
                    proxies= self.proxy_url
                    )
                self.save_cookies(session= session)
                # Снова загружаем cookies в сессию
                with open(Path(self.directory) / f'{self.filename}.json', 'r', encoding= 'utf-8') as fd:
                    cookies = json.load(fd)
                return cookies
        except EOFError:
            return None

    def create_session_with_retries(self):
        # Создаёт сессию с повторными попытками при ошибках.
        session = requests.Session()
        retry_strategy = Retry(
            # Общее количество допустимых повторных попыток.
            total= self.max_retries,
            # Коэффициент задержки между попытками после второй попытки
            backoff_factor=1,
            # Набор целочисленных кодов состояния HTTP, при которых следует принудительно выполнять повторную попытку.
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def auth(self, url_web):
        session = self.create_session_with_retries()

        # Попробуем загрузить существующие cookies
        session.cookies.update(self.load_cookies())

        try:
            ses = session.get(url_web)
            # Проверим, действительны ли cookies
            if ses.status_code == 200:
                print(f"Доступ получен, статус {ses.status_code}.")
                return session 
            else:
                print(f"Неудачная попытка подключения, статус {ses.status_code} пробуем еще...")
                self.create_session_with_retries()
        except requests.RequestException as err:
            print("Ошибка при запросе: ", err)


if __name__ == "__main__":
    url_size = <'url- адрес страницы входа'>
    auth_cookies = AuthCookies()
    auth_cookies.auth(url_web= url_size)