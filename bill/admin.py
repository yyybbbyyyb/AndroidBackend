from django.contrib import admin

# Register your models here.

from .models import Bill, Ledger, Budget, Category

admin.site.register(Bill)
admin.site.register(Ledger)
admin.site.register(Budget)
admin.site.register(Category)