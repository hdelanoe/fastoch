from django.contrib import admin

from inventory.models import Transaction, Product, Inventory

admin.site.register(Product)
admin.site.register(Transaction)
admin.site.register(Inventory)