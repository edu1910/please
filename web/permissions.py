from django.contrib.auth.decorators import user_passes_test

from monitor.models import GroupManager

def admin_required(*args):
    def test_func(user):
        return user.is_superuser

    return user_passes_test(test_func)

def manager_required(*args):
    def test_func(user):
        is_manager = user.is_superuser

        if not is_manager:
            is_manager = GroupManager.objects.filter(user=user).count() > 0

        return is_manager

    return user_passes_test(test_func)
