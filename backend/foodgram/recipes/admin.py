from django.contrib import admin

from recipes.models import (Recipe, Ingredient,
                            Tag, FavoriteRecipe,
                            RecipeIngredient, ShoppingCart)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    search_fields = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    list_filter = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'author_email')
    list_filter = ('tags',)
    search_fields = ('name', 'author__username', 'author__email')
    readonly_fields = ('favorited_count',)
    inlines = [RecipeIngredientInline]

    def favorited_count(self, obj):
        return obj.favorited_by.count()

    favorited_count.short_description = 'Количество добавлений в избранное'

    def author_email(self, obj):
        return obj.author.email

    author_email.short_description = 'Почта автора'


class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user', 'user_email')
    list_filter = ('recipe__tags',)
    search_fields = ('user__username', 'user__email', 'recipe__name')

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = 'Почта пользователя'


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user', 'user_email')
    search_fields = ('user__username', 'user__email')
    list_filter = ('recipe__tags',)

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = 'Email пользователя'


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(FavoriteRecipe, FavoriteRecipeAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
