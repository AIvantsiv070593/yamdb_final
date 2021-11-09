# yamdb_final
yamdb_final - API для проекта YamDB.
Проект Собирает отзывы пользователей о произведениях: фильмы, книги, музыка. Пользователи оставляют отзывы и рейтинги.

Разворенуть проект:
- Загрузить и запустить на сервере контейнер Docker
    docker pull aivanstiv070593/yamdb_final:v1
- На сервере выполнить из под root:
    docker-compose up -d # Запускаем приложение
    docker-compose exec web python manage.py makemigrations # Создаем миграции
    docker-compose exec web python manage.py migrate# Применяем миграции

    docker-compose exec web python manage.py createsuperuser # Создаем Админа
    docker-compose exec web python manage.py collectstatic # Собираем статику

Проверить работу:
http://51.250.23.14/admin/
http://51.250.23.14/api/v1/
http://51.250.23.14/redoc/


![yamdb_workflow workflow](https://github.com/AIvantsiv070593/yamdb_final/actions/workflows/yamdb_workflow.yml/badge.svg)