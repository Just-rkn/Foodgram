from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    '''Фильтр ингредиента по имени.'''

    name = filters.CharFilter(lookup_expr='startswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    '''Фильтр по тегам, избранному и корзине.'''

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
    )
    is_favorited = filters.BooleanFilter(method='is_favorited_filter')
    is_in_shopping_cart = filters.BooleanFilter(
        method='is_in_shopping_cart_filter'
    )

    def is_favorited_filter(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return self.request.user.favorites.all()
        return queryset.none()

    def is_in_shopping_cart_filter(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return self.request.user.shopping_cart.all()
        return queryset.none()

    class Meta:
        model = Recipe
        fields = ('tags', 'author',)
