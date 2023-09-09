from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название ингредиента')
    measurement_unit = models.CharField(max_length=50, verbose_name='Единица измерения')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Количество')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Tag(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название тега')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='Слаг тега')
    color = models.CharField(max_length=7, default='#007bff', verbose_name='Цвет тега')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Автор')
    title = models.CharField(max_length=255, verbose_name='Название рецепта')
    description = models.TextField(verbose_name='Описание рецепта')
    ingredients = models.ManyToManyField('Ingredient', through='RecipeIngredient', verbose_name='Ингредиенты')
    tags = models.ManyToManyField('Tag', verbose_name='Теги')
    image = models.ImageField(upload_to='recipes/', verbose_name='Изображение рецепта')
    cooking_time = models.PositiveIntegerField(verbose_name='Время приготовления (в минутах)')
    # pub_date = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Дата публикации')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('recipe', 'ingredient')

# class Subscription(models.Model):
#     user = models.ForeignKey(User, related_name='subscriptions', on_delete=models.CASCADE, verbose_name='Подписчик')
#     author = models.ForeignKey(User, related_name='subscribers', on_delete=models.CASCADE, verbose_name='Автор')
#
#     def __str__(self):
#         return f'{self.user} подписан на {self.author}'
#
#     class Meta:
#         unique_together = ['user', 'author']
#         verbose_name = 'Подписка'
#         verbose_name_plural = 'Подписки'


# class ShoppingList(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
#     recipes = models.ManyToManyField('Recipe', related_name='shopping_lists', verbose_name='Рецепты')
#
#     def __str__(self):
#         return f'Корзина покупок для {self.user}'
#
#     class Meta:
#         verbose_name = 'Корзина покупок'
#         verbose_name_plural = 'Корзины покупок'


# class Favorite(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
#     recipes = models.ManyToManyField('Recipe', related_name='favorited_by', verbose_name='Избранные рецепты')
#
#     def __str__(self):
#         return f'Избранное для {self.user}'
#
#     class Meta:
#         verbose_name = 'Избранное'
#         verbose_name_plural = 'Избранные'
