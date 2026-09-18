# HTTP API

Все тела и ответы используют JSON. Интерактивная документация генерируется по OpenAPI по адресу `/docs`.

| Метод | Адрес | Назначение |
|---|---|---|
| GET | `/health` | Проверить состояние сервиса |
| POST/GET | `/authors` | Создать / получить авторов |
| POST/GET | `/books` | Создать / найти книги (`title`, `author_id`) |
| POST/GET | `/branches` | Создать / получить филиалы |
| POST/GET | `/copies` | Создать / отфильтровать экземпляры (`branch_id`, `available`) |
| POST/GET | `/loans` | Выдать экземпляр / получить выдачи (`active_only`) |
| POST | `/loans/{loan_id}/return` | Вернуть экземпляр |

Пример создания книги:

```http
POST /books
Content-Type: application/json

{"title":"Мастер и Маргарита","isbn":"9785170906306","author_id":1}
```

Пример выдачи:

```http
POST /loans
Content-Type: application/json

{"copy_id":1,"reader_name":"Иван Петров"}
```

