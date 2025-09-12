from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SupplierCommodity, ListCommodity, Order, Rating
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from prophet import Prophet
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from django.db.models import Avg, Count
import matplotlib
matplotlib.use('Agg')  
import matplotlib.dates as mdates
from datetime import datetime
import io
import base64

@login_required
def add_commodity(request):
    """Allows suppliers to add a new commodity to their inventory."""
    if request.method == "POST":
        commodity_id = request.POST["commodity"]
        price = request.POST["price_per_unit"]
        manufacturer = request.POST["manufactured_company"]
        units = request.POST["available_units"]
        unit = request.POST["unit"]  # Get the selected unit from the form

        commodity = ListCommodity.objects.get(id=commodity_id)
        SupplierCommodity.objects.create(
            supplier=request.user,
            commodity=commodity,
            price_per_unit=price,
            manufactured_company=manufacturer,
            available_units=units,
            unit=unit  # Include the unit when creating the record
        )
        messages.success(request, "Commodity added successfully!")
        return redirect("supplier_dashboard")

@login_required
def update_commodity(request, commodity_id):
    """Allows suppliers to update their inventory details."""
    commodity = get_object_or_404(SupplierCommodity, id=commodity_id, supplier=request.user)

    if request.method == "POST":
        commodity.available_units = request.POST["available_units"]
        commodity.price_per_unit = request.POST["price_per_unit"]
        commodity.manufactured_company = request.POST["manufactured_company"]
        commodity.unit = request.POST["unit"]  # Update the unit field
        commodity.save()
        messages.success(request, "Commodity updated successfully!")
        return redirect("supplier_dashboard")
    
@login_required
def delete_commodity(request, commodity_id):
    """Allows suppliers to delete a commodity from their inventory."""
    commodity = get_object_or_404(SupplierCommodity, id=commodity_id, supplier=request.user)
    commodity.delete()
    messages.success(request, "Commodity deleted successfully!")
    return redirect("supplier_dashboard")

from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomUserCreationForm  # Import the new form

def signup(request):
    """Handles user signup."""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log in the new user
            return redirect("login")  # Redirect to dashboard after signup
    else:
        form = CustomUserCreationForm()
    return render(request, "inventory/signup.html", {"form": form})

def login_view(request):
    """Handles user login and redirects based on role."""
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Redirect based on user role
            if user.role == "supplier":
                return redirect("supplier_dashboard")
            elif user.role == "vendor":
                return redirect("vendor_dashboard")

            messages.error(request, "Invalid role.")
            return redirect("login")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "inventory/login.html", {"form": form})



def logout_view(request):
    """Logs the user out and redirects to login."""
    logout(request)
    return redirect("login")


from .forecast_utils import forecast_demand  # Make sure this is your utility function

@login_required
def supplier_dashboard(request):
    """Render the supplier's inventory dashboard and manage orders."""
    if request.user.role != "supplier":
        messages.error(request, "Access denied.")
        return redirect("login")

    inventory = SupplierCommodity.objects.filter(supplier=request.user)
    pending_orders = Order.objects.filter(supplier_commodity__supplier=request.user, status="pending")
    commodities = ListCommodity.objects.all()



    return render(
        request,
        "inventory/supplier_dashboard.html",
        {
            "inventory": inventory,
            "pending_orders": pending_orders,
            "commodities": commodities,
            
        }
    )

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import SupplierCommodity, ListCommodity, Order, User
@login_required
def vendor_dashboard(request):
    """Render the vendor's dashboard with search functionality and order placement."""
    if request.user.role != "vendor":
        messages.error(request, "Access denied.")
        return redirect("login")

    query = request.GET.get("search", "")
    
    # Get commodities with annotated supplier ratings
    supplier_commodities = SupplierCommodity.objects.select_related(
        'commodity', 'supplier'
    ).annotate(
        supplier_avg_rating=Avg('supplier__supplier_ratings__rating'),  # Changed to supplier_ratings
        supplier_rating_count=Count('supplier__supplier_ratings')      # Changed to supplier_ratings
    ).filter(available_units__gt=0)

    if query:
        supplier_commodities = supplier_commodities.filter(
            Q(commodity__name__icontains=query) |
            Q(supplier__username__icontains=query) |
            Q(supplier__address__icontains=query)
        )

    return render(
        request,
        "inventory/vendor_dashboard.html",
        {
            "supplier_commodities": supplier_commodities,
            "query": query,
        }
    )


@login_required                                                                                                                                                     
def place_order(request, commodity_id):
    """Allows vendors to place an order for a supplier's commodity."""
    if request.user.role != "vendor":
        messages.error(request, "Access denied.")
        return redirect("login")

    supplier_commodity = get_object_or_404(SupplierCommodity, id=commodity_id)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity"))

        if quantity <= 0:
            messages.error(request, "Invalid quantity.")
            return redirect("vendor_dashboard")

        if quantity > supplier_commodity.available_units:
            messages.error(request, "Insufficient stock.")
            return redirect("vendor_dashboard")

        Order.objects.create(
            vendor=request.user,
            supplier_commodity=supplier_commodity,
            quantity_requested=quantity,
            status="pending"
        )

        messages.success(request, "Order placed successfully.")
        return redirect("vendor_dashboard")
def home(request):
    return render(request, "inventory/home.html")

# views.py
from django.utils import timezone
from datetime import timedelta

@login_required
def supplier_orders(request):
    """View pending and previous orders for the current supplier with time filtering."""
    if request.user.role != "supplier":
        messages.error(request, "Access denied.")
        return redirect("login")

    # Pending orders (unchanged)
    pending_orders = Order.objects.filter(
        supplier_commodity__supplier=request.user,
        status="pending"
    ).order_by('-ordered_at')

    # Previous orders with time filtering
    time_filter = request.GET.get('time_filter', 'all')
    previous_orders = Order.objects.filter(
        supplier_commodity__supplier=request.user
    ).exclude(status="pending")

    # Apply time filters
    today = timezone.now().date()
    if time_filter == 'week':
        start_date = today - timedelta(days=7)
        previous_orders = previous_orders.filter(ordered_at__gte=start_date)
    elif time_filter == 'month':
        start_date = today - timedelta(days=30)
        previous_orders = previous_orders.filter(ordered_at__gte=start_date)
    elif time_filter == '3months':
        start_date = today - timedelta(days=90)
        previous_orders = previous_orders.filter(ordered_at__gte=start_date)
    elif time_filter == 'year':
        start_date = today - timedelta(days=365)
        previous_orders = previous_orders.filter(ordered_at__gte=start_date)
    # 'all' shows everything

    previous_orders = previous_orders.order_by('-ordered_at')

    return render(request, "inventory/orders.html", {
        "pending_orders": pending_orders,
        "previous_orders": previous_orders,
        "current_filter": time_filter  # Pass current filter to template if needed
    })
@login_required
def accept_order(request, order_id):
    """Supplier accepts an order, reducing stock."""
    order = get_object_or_404(
        Order, 
        id=order_id, 
        supplier_commodity__supplier=request.user,  # Critical security check
        status='pending'  # Only pending orders can be accepted
    )

    if order.quantity_requested > order.supplier_commodity.available_units:
        messages.error(request, "Not enough stock.")
    else:
        order.accept_order()
        messages.success(request, "Order accepted.")

    return redirect("supplier_orders")  # Redirect back to orders list

@login_required
def reject_order(request, order_id):
    """Supplier rejects an order."""
    order = get_object_or_404(
        Order, 
        id=order_id, 
        supplier_commodity__supplier=request.user,  # Critical security check
        status='pending'  # Only pending orders can be rejected
    )
    order.reject_order()
    messages.success(request, "Order rejected.")
    return redirect("supplier_orders")  # Redirect back to orders list

@login_required
def order_request(request):
    """Display all orders (pending, accepted, rejected) for the logged-in vendor."""
    if request.user.role != "vendor":
        messages.error(request, "Access denied.")
        return redirect("login")

    # Fetch orders placed by the logged-in vendor
    orders = Order.objects.filter(vendor=request.user).order_by('-ordered_at')

    return render(request, "inventory/order_request.html", {"orders": orders})



@login_required
def rate_order(request, order_id):
    """Allow vendors to rate completed orders."""
    if request.user.role != "vendor":
        messages.error(request, "Access denied.")
        return redirect("login")

    order = get_object_or_404(Order, id=order_id, vendor=request.user, status='accepted')
    
    if order.vendor != request.user:
        messages.error(request, "You can only rate your own orders.")
        return redirect("order_request")

    if Rating.objects.filter(order=order, vendor=request.user).exists():
        messages.error(request, "You have already rated this order.")
        return redirect("order_request")

    if request.method == "POST":
        rating_value = int(request.POST.get("rating"))
        comment = request.POST.get("comment", "")

        if 1 <= rating_value <= 5:
            Rating.objects.create(
                order=order,
                vendor=request.user,
                supplier=order.supplier_commodity.supplier,
                rating=rating_value,
                comment=comment
            )
            messages.success(request, "Thank you for your rating!")
            return redirect("order_request")
        else:
            messages.error(request, "Invalid rating value.")

    return render(request, "inventory/rate_order.html", {"order": order})

@login_required
def supplier_ratings(request):
    """Display all ratings received by the supplier."""
    if request.user.role != "supplier":
        messages.error(request, "Access denied.")
        return redirect("login")

    ratings = Rating.objects.filter(supplier=request.user).order_by('-created_at')


    rating_stats = ratings.aggregate(
        avg_rating=Avg('rating'),
        total_ratings=Count('id')
    )

    return render(request, "inventory/supplier_ratings.html", {
        "ratings": ratings,
        "avg_rating": rating_stats['avg_rating'],
        "total_ratings_given": rating_stats['total_ratings'],
    })


def generate_trend_insight(commodity_name, weekly_demand):
    if len(weekly_demand) < 2:
        return f"Not enough data to identify a demand trend for {commodity_name}."

    current_week = weekly_demand.iloc[-1]['y']
    previous_week = weekly_demand.iloc[-2]['y']

    if previous_week == 0:
        return f"No prior demand history for {commodity_name} to compare trends."

    change_pct = ((current_week - previous_week) / previous_week) * 100
    abs_change = abs(change_pct)

    std_dev = weekly_demand['y'].std()
    volatility_flag = std_dev > 0.3 * weekly_demand['y'].mean() if weekly_demand['y'].mean() != 0 else False

    if abs_change < 5:
        trend_desc = "remained stable"
    elif abs_change < 15:
        trend_desc = "changed slightly"
    elif abs_change < 30:
        trend_desc = "changed moderately"
    else:
        trend_desc = "changed significantly"

    direction = "increased" if change_pct > 0 else "decreased"
    base_insight = (
        f"Demand for {commodity_name} {direction} by {abs_change:.1f}% this week "
        f"compared to the previous week. This is considered a {trend_desc} trend."
    )

    if volatility_flag:
        base_insight += " Note: demand has shown high volatility recently."

    return base_insight

def forecast_supplier_demands(request):
    user = request.user
    supplier_id = user.id
    supplier_commodities = SupplierCommodity.objects.filter(supplier_id=supplier_id)

    prediction_list = []

    for sc in supplier_commodities:
        orders = Order.objects.filter(
            supplier_commodity_id=sc.id, status='accepted'
        ).order_by('ordered_at')

        if orders.count() < 5:
            prediction_list.append({
                'commodity': sc.commodity.name,
                'commodity_id': sc.commodity.id,
                'status': 'insufficient',
                'data': None,
                'graph': None,
                'insight': f"Not enough data to forecast or analyze trends for {sc.commodity.name}."
            })
            continue

        df = pd.DataFrame(list(orders.values('ordered_at', 'quantity_requested')))
        df['ds'] = pd.to_datetime(df['ordered_at']).dt.tz_localize(None)
        df = df.groupby('ds')['quantity_requested'].sum().reset_index()
        df.rename(columns={'quantity_requested': 'y'}, inplace=True)

        # Weekly demand for trend insight
        df['week'] = df['ds'].dt.isocalendar().week
        df['year'] = df['ds'].dt.isocalendar().year
        weekly_demand = df.groupby(['year', 'week'])['y'].sum().reset_index()
        insight = generate_trend_insight(sc.commodity.name, weekly_demand)

        # Forecast using Prophet
        model = Prophet()
        model.fit(df)

        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)

        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(7)
        result['yhat'] = result['yhat'].apply(lambda x: max(0, x))
        result['yhat_lower'] = result['yhat_lower'].apply(lambda x: max(0, x))
        result['yhat_upper'] = result['yhat_upper'].apply(lambda x: max(0, x))

        # Generate plot
        plt.figure(figsize=(10, 5))
        plt.plot(df['ds'], df['y'], 'k.', label='Historical Data')
        plt.plot(forecast['ds'], forecast['yhat'], ls='-', color='#0072B2', label='Forecast')
        plt.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'],
                         color='#0072B2', alpha=0.2, label='Uncertainty Interval')

        forecast_start = forecast['ds'].max() - pd.Timedelta(days=6)
        plt.axvline(x=forecast_start, color='gray', linestyle='--', alpha=0.5)
        plt.text(forecast_start, plt.ylim()[1]*0.9, ' Forecast', color='gray')

        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(df)//5)))
        plt.xticks(rotation=45)
        plt.grid(alpha=0.3)
        plt.legend()
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        graph = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()

        prediction_list.append({
            'commodity': sc.commodity.name,
            'commodity_id': sc.commodity.id,
            'status': 'ok',
            'data': result.to_dict(orient='records'),
            'graph': graph,
            'insight': insight
        })

    prediction_list.sort(key=lambda x: 0 if x['status'] == 'ok' else 1)

    return render(request, 'inventory/forecast.html', {
        'predictions': prediction_list,
        'now': datetime.now().strftime("%Y-%m-%d")
    })














# def forecast_supplier_demands(request):
#     user = request.user
#     supplier_id = user.id
#     supplier_commodities = SupplierCommodity.objects.filter(supplier_id=supplier_id)
    
#     prediction_list = []

#     for sc in supplier_commodities:
#         orders = Order.objects.filter(
#             supplier_commodity_id=sc.id, status='accepted'
#         ).order_by('ordered_at')

#         if orders.count() < 5:
#             prediction_list.append({
#                 'commodity': sc.commodity.name,
#                 'status': 'insufficient',
#                 'data': None
#             })
#             continue

#         df = pd.DataFrame(list(orders.values('ordered_at', 'quantity_requested')))
#         df['ds'] = pd.to_datetime(df['ordered_at']).dt.tz_localize(None)
#         df = df.groupby('ds')['quantity_requested'].sum().reset_index()
#         df.rename(columns={'quantity_requested': 'y'}, inplace=True)

#         model = Prophet()
#         model.fit(df)

#         future = model.make_future_dataframe(periods=7)
#         forecast = model.predict(future)

#         result = forecast[['ds', 'yhat']].tail(7)
#         result['yhat'] = result['yhat'].apply(lambda x: max(0, x))

#         prediction_list.append({
#             'commodity': sc.commodity.name,
#             'status': 'ok',
#             'data': result.to_dict(orient='records')
#         })

#     # Sort so "ok" comes first, "insufficient" last
#     prediction_list.sort(key=lambda x: 0 if x['status'] == 'ok' else 1)

#     return render(request, 'inventory/forecast.html', {'predictions': prediction_list})







