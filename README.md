# ckl-rest-auth
An opinionated Django app to provide user authentication.

## Installation

1. `pip install cklauth`
1. Add to your project's `INSTALLED_APPS`:
  - `rest_framework`
  - `rest_framework.authtoken`
  - `corsheaders`
  - `cklauth`
1. Include `ckl-rest-auth` urls to your project:
   On `urls.py` add `path('', include('cklauth.urls'))`
1. Add settings according to the project requirements
  - For Django's default user config:
  ```python
  # Field used for authencation together with password (required)
  'LOGIN_FIELD': 'email',

  # Fields used on user serializer
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
  ```  
  Note that the default `LOGIN_FIELD` is `email` and then you need to use the helper
  authentication backend:  
  ```python
  AUTHENTICATION_BACKENDS = ['cklauth.auth.EmailOrUsernameModelBackend']
  ```

  - For a custom user model, you can define additional options:
  ```python
  CKL_REST_AUTH = {
    # Field used for authencation together with password (required)
    'LOGIN_FIELD': 'email',

    # Override the default serializer used on registration and authentication responses (optional)
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
        # Define a callable that receives the social user payload and returns the value on of the
        # User model USERNAME_FIELD (username, for instance). The default function already checks
        # if the value is in use. Set it to `None`, if you don't want to generate a USERNAME_FIELD.
        'AUTH_FIELD_GENERATOR': 'cklauth.utils.auth_field_generator',
        # How to map the social user payload to the User model fields. It accepts a callable that
        # receives the whole social user payload to map more complex data.
        'USER_INFO_MAPPING': {
            'full_name': 'full_name': lambda info: '{} {}'.format(
                info.get('given_name'),
                info.get('family_name')
            ),
            'email': 'email',
        },
    },

    # Facebook authentication settings (optional)
    'FACEBOOK': {
        'CLIENT_ID': 'insert-your-key',
        'CLIENT_SECRET': 'insert-your-key',
        'REDIRECT_URI': 'insert-your-uri',
        'AUTH_FIELD_GENERATOR': 'cklauth.utils.auth_field_generator',
        'USER_INFO_MAPPING': {
            'full_name': 'full_name': lambda info: '{} {}'.format(
                info.get('first_name'),
                info.get('last_name')
            ),
            'email': 'email',
        },
    },
  }
  ```

## Basic Endpoints

`POST /api/v1/login`  
Body (depends on LOGIN_FIELD)
```json
{
  "email": "example@example.com",
  "password": "secret"
}
```
Response (depends on REGISTER_FIELDS and USER_SERIALIZER) - 200 OK
```json
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
```json
{
  "email": "example@example.com",
  "password": "secret",
  "first_name": "Example",
  "last_name": "Example"
}
```
Response (depends on REGISTER_FIELDS and USER_SERIALIZER) - 201 CREATED
```json
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
```json
{
  "email": "example@example.com"
}
```
Response - 200 OK
```json
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
```json
{
  "code": "<code from previous step>",
  "user_extra_fields": {
    "role": "admin"
  }
}
```  
**Note:** You can pass additional user fields in the `user_extra_fields` key, as long as they are
part of the main `REGISTER_FIELDS` list.

Response - 200 OK
```json
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
