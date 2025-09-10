from django.urls import path
from .views import (
    signup, supplier_dashboard, vendor_dashboard, 
    add_commodity, update_commodity, delete_commodity, 
    login_view, logout_view, place_order, accept_order, reject_order,supplier_orders,home,
    order_request, forecast_supplier_demands, rate_order, supplier_ratings
)


urlpatterns = [
    path("signup/", signup, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    path("dashboard/supplier/", supplier_dashboard, name="supplier_dashboard"),
    path("dashboard/supplier/add/", add_commodity, name="add_commodity"),
    path("dashboard/supplier/update/<int:commodity_id>/", update_commodity, name="update_commodity"),
    path("dashboard/supplier/delete/<int:commodity_id>/", delete_commodity, name="delete_commodity"),
    path("supplier/orders/", supplier_orders, name="supplier_orders"),

    path("dashboard/vendor/", vendor_dashboard, name="vendor_dashboard"),
    path("dashboard/vendor/place_order/<int:commodity_id>/", place_order, name="place_order"),

    path("dashboard/supplier/accept_order/<int:order_id>/", accept_order, name="accept_order"),
    path("dashboard/supplier/reject_order/<int:order_id>/", reject_order, name="reject_order"),
    path("", home, name="home"),

    path("dashboard/vendor/order_request",order_request,name="order_request"),
    path('dashboard/supplier/forecast/', forecast_supplier_demands, name='forecast'),
    path('dashboard/vendor/rate_order/<int:order_id>/', rate_order, name='rate_order'),
    path('dashboard/supplier/ratings/', supplier_ratings, name='supplier_ratings'),
]
