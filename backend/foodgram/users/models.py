from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True)


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('user', 'author'),
                                    name='unique_follow'),
        )

    def __str__(self):
        return f'Автор: {self.author}, подписчик: {self.user}'
