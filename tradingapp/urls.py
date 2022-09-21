from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('addstocks/', views.add_stock, name='add_stocks'),
    path('output/', views.output, name='output'),
    path('delete/<stock_id>',views.delete, name='delete') 
]
