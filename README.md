## Проект foodgram

Foodgram - продуктовый помощник с базой кулинарных рецептов.
Доступен по адресу 158.160.28.231:8000

## Технологии:

Python, Django, Django Rest Framework, Docker, Gunicorn, NGINX, PostgreSQL.

## Запуск проекта на локальной машине:

- Клонировать репозиторий:
https://github.com/justrkn/foodgram-project-react.git

- Cоздать файл .env и заполнить своими данными по аналогии с example.env:

- Создать и запустить контейнеры Docker, последовательно выполнить команды по созданию миграций, сбору статики, 
созданию суперпользователя, как указано ниже.

- sudo docker compose up -d
- sudo docker compose exec backend python manage.py makemigrations
- sudo docker compose exec backend python manage.py migrate
- sudo docker compose exec backend python manage.py createsuperuser
- sudo docker compose exec backend python manage.py collectstatic
- sudo docker compose exec backend cp -r /app/static/. /static/static/
- sudo docker compose exec backend python manage.py ingredients_upload data/ingredients.csv

## Автор 
justrkn