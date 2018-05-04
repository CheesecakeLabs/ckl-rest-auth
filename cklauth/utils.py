from os import urandom
from binascii import hexlify

from django.contrib.auth import get_user_model


User = get_user_model()


def auth_field_generator(user_fields, add_suffix=False):
    """
    Generate a login field based on the user first and last name and check if it is in use by any
    user. Recursively adds a hash suffix in case of repeated login field values.

    Args:
        user_fields (dict): user information.
        add_suffix (bool): whether it should calculate and add a random hash to the end of the
            field. Add with the following format `<first-name>-<last-name>-<suffix>`.

    Returns:
        (str) The composed unique login field value.
    """
    base = '-'.join(filter(None, [
        user_fields.get('first_name').lower().replace(" ", "_"),
        user_fields.get('last_name').lower().replace(" ", "_")
    ]))
    suffix = hexlify(urandom(3)) if add_suffix else None
    login_field = '-'.join(filter(None, [base, suffix]))

    if User.objects.filter(**{User.USERNAME_FIELD: base}).exists():
        return auth_field_generator(login_field, add_suffix=True)

    return login_field
