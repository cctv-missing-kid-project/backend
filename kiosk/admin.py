from django.contrib import admin
from kiosk.models import CustomerGroup, Customer, Camera

# Register your models here.
admin.site.register(CustomerGroup)
admin.site.register(Customer)
admin.site.register(Camera)
