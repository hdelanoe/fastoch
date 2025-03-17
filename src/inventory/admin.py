from django.contrib import admin

from inventory.models import Inventory, Product, iProduct

admin.site.register(Inventory)
admin.site.register(Product)
admin.site.register(iProduct)