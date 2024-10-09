from django.contrib import admin

from inventory.models import StockTransaction, Product, Inventory

admin.site.register(Product)
admin.site.register(StockTransaction)
admin.site.register(Inventory)