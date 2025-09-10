from django.contrib import admin
from .models import User, ListCommodity, SupplierCommodity,Order



admin.site.register(User)
admin.site.register(ListCommodity)
admin.site.register(SupplierCommodity)
admin.site.register(Order) 