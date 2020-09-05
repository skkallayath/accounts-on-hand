from django.contrib import admin

from .models import Account, Category, Commitment, Transaction

# Register your models here.

admin.site.register(Category)
admin.site.register(Account)
admin.site.register(Commitment)
admin.site.register(Transaction)