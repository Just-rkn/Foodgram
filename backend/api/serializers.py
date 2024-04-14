from django.db import transaction
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, validators

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Subscription, User


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Коротый сериализатор рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = tuple(User.REQUIRED_FIELDS) + (
            User.USERNAME_FIELD,
            'password',
        )


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous or user == obj:
            return False
        return Subscription.objects.filter(
            user=user, author=obj
        ).exists()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        read_only_fields = ('id', 'is_subscribed',)


class SubscriptionSerializer(UserSerializer):
    """Сериализатор подписки."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            try:
                limit = int(limit)
                recipes = recipes[:limit]
            except ValueError:
                pass
        serializer = ShortRecipeSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )


class CreateSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    def to_representation(self, instance):
        return SubscriptionSerializer(
            instance.author,
            context={'request': self.context.get('request')}
        ).data

    class Meta:
        model = Subscription
        fields = ('user', 'author', )
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
            )
        ]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')


class CreateRecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор создании ингредиентов в рецепте."""

    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField()

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Количество Ингредиента должно быть не меньше одного.'
            )
        return value

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='ingredient_list'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    def request_user_recipe_exists(self, recipe_queryset):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return recipe_queryset.filter(user=user).exists()

    def get_is_favorited(self, obj):
        return self.request_user_recipe_exists(obj.favorites)

    def get_is_in_shopping_cart(self, obj):
        return self.request_user_recipe_exists(obj.shopping_cart)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )


class CreateRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор создания рецептов."""

    ingredients = CreateRecipeIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(represent_in_base64=True)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context=self.context
        )
        return serializer.data

    def validate_ingredients(self, value):
        unique_ingredients = {ingredient['id'] for ingredient in value}
        if len(unique_ingredients) != len(value):
            raise serializers.ValidationError('Ингредиенты повторяются.')
        return value

    def validate_tags(self, value):
        if len(set(value)) != len(value):
            raise serializers.ValidationError('Теги повторяются.')
        return value

    def create_ingredients(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=get_object_or_404(
                        Ingredient, pk=ingredient['id']
                    ),
                    amount=ingredient['amount']
                )
                for ingredient in ingredients
            ]
        )

    def add_ingredients_and_tags_to_recipe(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        self.create_ingredients(recipe, ingredients)
        recipe.tags.set(tags)

    @transaction.atomic
    def create(self, validated_data):
        author = self.context.get('request').user
        recipe = Recipe.objects.create(
            author=author,
            name=validated_data.pop('name'),
            image=validated_data.pop('image'),
            text=validated_data.pop('text'),
            cooking_time=validated_data.pop('cooking_time')
        )
        self.add_ingredients_and_tags_to_recipe(recipe, validated_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        RecipeIngredient.objects.filter(recipe=instance).delete()
        validated_data = self.add_ingredients_and_tags_to_recipe(
            instance, validated_data
        )
        return super().update(instance, validated_data)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'name',
            'image',
            'text',
            'cooking_time'
        )
