from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorPermission
from .serializers import (CreateRecipeSerializer, IngredientSerializer,
                          RecipeSerializer, ShortRecipeSerializer,
                          SubscribeSerializer, TagSerializer, UserSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription, User


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    '''ViewSet тега.'''

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    '''ViewSet ингредиента.'''

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class UserViewSet(viewsets.GenericViewSet):
    '''ViewSet пользователя.'''

    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=True,
        url_path='subscribe',
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscribe(self, request, pk):
        author = get_object_or_404(User, id=pk)
        if request.method == 'post':
            serializer = SubscribeSerializer(
                data={'user': request.user, 'author': author},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        Subscription.objects.filter(user=request.user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        url_path='subscriptions',
        methods=('get',),
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscriptions(self, request):
        queryset = Subscription.objects.filter(user=request.user)
        paginator = LimitOffsetPagination()
        pages = paginator.paginate_queryset(queryset, request)
        serializer = SubscribeSerializer(
            pages,
            many=True,
            context={'request': request},
        )
        return paginator.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    '''ViewSet рецепта.'''

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeSerializer
        return CreateRecipeSerializer

    def create_or_delete_recipe_m_to_m(self, request, pk, queryset):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if queryset.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset.create(user=request.user, recipe=recipe).save()
            serializer = ShortRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not queryset.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт не был добавлен изначально.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        url_path='favorite',
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request, pk):
        return self.create_or_delete_recipe_m_to_m(
            request, pk, Favorite.objects
        )

    @action(
        detail=True,
        url_path='shopping_cart',
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        return self.create_or_delete_recipe_m_to_m(
            request, pk, ShoppingCart.objects
        )

    @action(
        detail=False,
        url_path='download_shopping_cart',
        methods=('get',),
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        shopping_list = ['Список покупок\n']

        for ingredient in ingredients:
            shopping_list.append(
                f'{ingredient["ingredient__name"]} - '
                f'{ingredient["amount"]} '
                f'({ingredient["ingredient__measurement_unit"]})\n'
            )
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
