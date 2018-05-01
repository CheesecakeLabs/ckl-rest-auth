# ckl-rest-auth
An opinionated Django app to provide user authentication.

## Installation

1. `pip install cklauth`
1. Add to your project's `INSTALLED_APPS`:
  - `rest_framework`
  - `rest_framework.authtoken`
  - `corsheaders`
  - `cklauth`
1. Include ckl-rest-auth urls to your project:
   On urls.py add `path('', include('cklauth.urls'))`
1. Add settings according to the project requirements:
```
AUTHENTICATION_BACKENDS = ['cklauth.auth.EmailOrUsernameModelBackend']

CKL_REST_AUTH = {
    # Field used for authencation together with password (required - 'email' or 'password')
    'LOGIN_FIELD': 'email',

    # Serializer used on registration and authentication responses (optional)
    'USER_SERIALIZER': 'cklauth.api.v1.serializers.UserSerializer',

    # Fields used on user serializer (not used if USER_SERIALIZER is defined above)
    'REGISTER_FIELDS': ('username', 'email'),

    # From email used on password reset emails (optional)
    'FROM_EMAIL': 'default@email.com',

    # Google authentication settings (optional)
    'GOOGLE': {
        'CLIENT_ID': 'insert-your-key',
        'CLIENT_SECRET': 'insert-your-key',
        'REDIRECT_URI': 'insert-your-uri',
    },

    # Facebook authentication settings (optional)
    'FACEBOOK': {
        'CLIENT_ID': 'insert-your-key',
        'CLIENT_SECRET': 'insert-your-key',
        'REDIRECT_URI': 'insert-your-uri',
    },
}
```

## Basic Endpoints

`POST /api/v1/login`
Body (depends on LOGIN_FIELD)
```
{
  "email": "example@example.com",
  "password": "secret"
}
```
Response (depends on REGISTER_FIELDS and USER_SERIALIZER) - 200 OK
```
{
  "token": "supersecret",
  "user": {
    "id": 1,
    "email": "example@example.com",
    "first_name": "Example",
    "last_name": "Example"
  }
}
```
**Note:** the user payload may vary according to specified REGISTER_FIELDS and USER_SERIALIZER.

`POST /api/v1/register`
Body (depends on REGISTER_FIELDS and USER_SERIALIZER -- always has a password)
```
{
  "email": "example@example.com",
  "password": "secret",
  "first_name": "Example",
  "last_name": "Example"
}
```
Response (depends on REGISTER_FIELDS and USER_SERIALIZER) - 201 CREATED
```
{
  "token": "supersecret",
  "user": {
    "id": 1,
    "email": "example@example.com",
    "first_name": "Example",
    "last_name": "Example"
  }
}
```
**Note:** the user payload may vary according to specified REGISTER_FIELDS and USER_SERIALIZER.

`POST /api/v1/password-reset/`
Body
```
{
  "email": "example@example.com"
}
```
Response - 200 OK
```
{
  "email": "example@example.com"
}
```
Note: it always returns success, even if the provided email is not registered.


## Social Endpoints

`GET /api/v1/social/google`
`GET /api/v1/social/facebook`
**Note:** this should not be XHR request, the user will be redirected to consent screen. After
consent, the user is redirected to platform REDIRECT_URI added on settings, where a code is
extracted from the URL hash.

`POST /api/v1/social/google`
`POST /api/v1/social/facebook`
Body
```
{
  "code": "<code from previous step>"
}
```
Response - 200 OK
```
{
  "token": "supersecret",
  "user": {
    "id": 1,
    "email": "example@example.com",
    "first_name": "Example",
    "last_name": "Example"
  }
}
```
**Note:** the user payload may vary according to specified REGISTER_FIELDS and USER_SERIALIZER.

## Contributing

The library code is under `cklauth` folder and tests are in a test project under `testapp`
folder.

### Running tests:

* Ensure that you have the app requirements installed
```
pip install -r requirements.txt
pip install -e cklauth
```

* Run the tests
```
python -m pytest test_default_user
python -m pytest test_custom_user
```
