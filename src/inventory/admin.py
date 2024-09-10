from django.contrib import admin

from inventory.models import StockEntry, Product, Inventory

admin.site.register(StockEntry)
admin.site.register(Product)
admin.site.register(Inventory)