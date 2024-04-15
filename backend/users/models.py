from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import F, Q

MAX_LENGTH_NAME = 150

username_validator = UnicodeUsernameValidator()


class User(AbstractUser):
    """Модель пользователя."""

    email = models.EmailField('Почта', unique=True)
    first_name = models.CharField('имя', max_length=MAX_LENGTH_NAME)
    last_name = models.CharField('фамилия', max_length=MAX_LENGTH_NAME)
    username = models.CharField(
        'логин',
        max_length=MAX_LENGTH_NAME,
        unique=True,
        validators=(username_validator,),
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name',)

    def __str__(self) -> str:
        return self.username

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.UniqueConstraint(
                fields=('username', 'email'), name='unique_username_email'
            ),
        ]


class Subscription(models.Model):
    """Модель подписок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    def __str__(self) -> str:
        return f'{self.user.username} подписан на {self.author.username}'

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        indexes = [
            models.Index(fields=('user', 'author'), name='follow'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_follow'
            ),
            models.CheckConstraint(
                check=~Q(author=F('user')),
                name='user_not_author'
            ),
        ]
