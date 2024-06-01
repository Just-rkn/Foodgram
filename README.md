## Проект Foodgram
Foodgram - продуктовый помощник с базой кулинарных рецептов.

## Необходимые инструменты
    Git
    Docker

## Технологии:
    Python
    Django
    Django Rest Framework
    Docker
    Gunicorn
    Nginx
    PostgreSQL

## Запуск проекта на локальной машине:

- Клонировать репозиторий:
https://github.com/justrkn/Foodgram.git

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
  Староверов Федор
