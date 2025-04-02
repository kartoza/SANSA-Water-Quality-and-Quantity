import os
from django.contrib.auth import get_user_model


def get_admin_user():
    return get_user_model().objects.filter(
        username=os.getenv("ADMIN_USERNAME")
    ).first()
