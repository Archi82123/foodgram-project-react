# Generated by Django 4.2.4 on 2023-10-01 13:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0009_alter_recipe_cooking_time_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recipe',
            options={'ordering': ['-id'], 'verbose_name': 'Рецепт', 'verbose_name_plural': 'Рецепты'},
        ),
    ]
