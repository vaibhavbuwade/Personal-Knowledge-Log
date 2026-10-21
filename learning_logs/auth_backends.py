from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend allowing users to log in using either
    their username or their registered email address.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD) or kwargs.get('email')

        if not username or not password:
            return None

        # Search for matching user by username or email (case-insensitive)
        user = User.objects.filter(
            Q(username__iexact=username.strip()) | Q(email__iexact=username.strip().lower())
        ).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
