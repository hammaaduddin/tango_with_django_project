from django.contrib import admin
from rango.models import Category, Page, PageAdmin

admin.site.register(Page, PageAdmin)

#Add in this class to customise the Admin INterface
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}

#Update the registration to include this customised interface
admin.site.register(Category, CategoryAdmin) 
   
