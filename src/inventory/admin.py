from django.contrib import admin

from inventory.models import Inventory, Product, iProduct, DLC

admin.site.register(Inventory)
admin.site.register(Product)
admin.site.register(iProduct)
admin.site.register(DLC)