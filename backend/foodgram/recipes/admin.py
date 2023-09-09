from django.contrib import admin
from .models import Recipe, Ingredient, Tag # , Subscription, ShoppingList, Favorite

admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(Tag)
# admin.site.register(Subscription)
# admin.site.register(ShoppingList)
# admin.site.register(Favorite)
