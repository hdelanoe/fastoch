from django.contrib import admin

from inventory.models import Provider, StockTransaction, Product, Inventory

admin.site.register(Provider)
admin.site.register(Product)
admin.site.register(StockTransaction)
admin.site.register(Inventory)