from django.contrib import admin

from .models import Subscription, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Отображение модели User в админ части сайта."""

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_superuser',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    list_filter = ('is_superuser',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Отображение модели Subscription в админ части сайта."""

    list_display = ('user', 'author',)
    search_fields = ('user__username', 'author__username')
