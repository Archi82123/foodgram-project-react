import django_filters
from django_filters.rest_framework import filters

from recipes.models import Recipe, Ingredient, Tag


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.NumberFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart',
    )
    author = django_filters.NumberFilter(
        field_name='author__id',
        method='filter_by_author',
    )
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value == 1 and user.is_authenticated:
            return queryset.filter(favorited_by__user=user)
        elif value == 0 and user.is_authenticated:
            return queryset.exclude(favorited_by__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value == 1 and user.is_authenticated:
            return queryset.filter(users_cart__user=user)
        elif value == 0 and user.is_authenticated:
            return queryset.exclude(users_cart__user=user)
        return queryset

    def filter_by_author(self, queryset, name, value):
        return queryset.filter(author__id=value)


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
        strict = False
