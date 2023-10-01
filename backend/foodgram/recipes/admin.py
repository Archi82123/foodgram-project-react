from django.contrib import admin

from recipes.models import Recipe, Ingredient, Tag, FavoriteRecipe


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    list_filter = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    readonly_fields = ('favorited_count',)

    def favorited_count(self, obj):
        return obj.favorited_by.count()

    favorited_count.short_description = 'Количество добавлений в избранное'


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(FavoriteRecipe)
