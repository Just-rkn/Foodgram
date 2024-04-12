from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()

MIN_AMOUNT_VALUE: int = 1
HEX_LENGTH: int = 7
LONG_LENGTH: int = 200


class BaseNameModel(models.Model):
    """Абстрактная модель для добавления поля name."""

    name = models.CharField(
        'Название', max_length=LONG_LENGTH
    )

    class Meta:
        abstract = True


class Tag(BaseNameModel):
    """Модель тегов."""

    slug = models.SlugField(
        'Слаг', max_length=LONG_LENGTH, unique=True
    )
    color = models.CharField(
        'Цвет',
        max_length=HEX_LENGTH,
        unique=True
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredient(BaseNameModel):
    """Модель ингредиентов."""

    measurement_unit = models.CharField(
        'Единица измерения', max_length=LONG_LENGTH
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredients',
            )
        ]


class Recipe(BaseNameModel):
    """Модель рецептов."""

    pub_date = models.DateTimeField(
        'Дата добавления', auto_now_add=True
    )
    image = models.ImageField(
        'Фото', upload_to='recipes/images'
    )
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(MIN_AMOUNT_VALUE)]
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes_list',
        verbose_name='Ингредиенты'
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class RecipeIngredient(models.Model):
    """Модель для связи рецептов и ингредиентов."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='ingredient_list'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipes'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(MIN_AMOUNT_VALUE)]
    )

    def __str__(self) -> str:
        return f'{self.ingredient} есть в {self.recipe}'

    class Meta:
        verbose_name = 'Ингредиенты в рецете'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            )
        ]


class Favorite(models.Model):
    """Модель избранного."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites'
    )

    def __str__(self) -> str:
        return f'{self.recipe} в избранном у {self.user}'

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_favorite'
            )
        ]


class ShoppingCart(models.Model):
    """Модель корзины покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    def __str__(self) -> str:
        return f'{self.recipe} в корзине у {self.user}'

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзина покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe'
            )
        ]
