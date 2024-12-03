from django.contrib import admin

from inventory.models import Transaction, Product, iProduct, Inventory, Receipt

admin.site.register(Product)
admin.site.register(iProduct)
admin.site.register(Transaction)
admin.site.register(Inventory)
admin.site.register(Receipt)