## Читай!
> Итак, это не готовая работа - это черновик задания, иными словами говнокод. Моя личная оценка этого кода на 2+ из 5. Нарушен принцип DRY, не используются удобные библиотеки, типа aiohtp_session, aiohttp_security, marshmallow и др., благодаря которым код станет чище и лаконичнее. Слои проекта сделаны ужасно, куча исключений не обработана, сериализации данных нет. Задание делал в течение дня, поэтому не успел более подробно разобраться в стеке Alembic, Swagger, Docker. Тесты не делал, так как не успел даже основной код привести в порядок. Но обязательная часть задания выполнена, наверное)))


## About project
This is a user data API server developed on the principle of CRUD - create, read, update, delete
Authentication and authorization are required to work with CRUD, 
### Authentication
Authentication at http://localhost:8080/login, will accept the POST method, and in the JSON body:
>{
>    "login": "admin",
>    "password": "admin"
>}

Returns the auth_token cookie

### Logout
Logout at http://localhost:8080/login, will accept the clear POST method
Deletes the token from the database and clears the cookie
Returns HTTPOk

### CRUD
All CRUD methods are located at http://localhost:8080/user, GET, POST, DELETE, PATCH

#### GET
Accepts an empty request
The GET method returns a list of all users in JSON

#### POST
Takes JSON data in the body
>{
  "first_name": "Dunya",
  "last_name": "Kulakova",
  "login": "mashka777",
  "password": "huinyaska777",
  "birth_date": "1975-12-22",
  "blocked": false,
  "is_admin": true
}
Returns HTTPOk when the user is successfully added

#### DELETE
Takes user id JSON
>{
    "id": 3
}
Returns HTTPOk

#### PATCH
Takes user dataset JSON to update it by id
>{
  "id": 2,
  "first_name": "Katya",
  "last_name": "Katerina",
  "login": "Opa3333",
  "password": "fghfghdfgh",
  "birth_date": "1975-12-22",
  "blocked": true,
  "is_admin": false
}
Returns HTTPOk

## Requirements
- You will need Python 3.10.5, 
- PostgreSQL 12.9 +
- Database created with the name "simaland". User "sima", password "sima" and its owner database

## Manual
Create env or docker container
Activate virtual environment (not for docker)
Install pip packages from requrements.txt
```sh
pip install -r requirements.txt
```
init BD tables and first user admin:
```sh
python db.py
```
To run the application:
```sh
python app.py
```
