# from prophet import Prophet
# from django.http import JsonResponse
# from inventory.models import Order, SupplierCommodity
# import pandas as pd
# import logging
# logger = logging.getLogger(__name__)

# def forecast_demand(request, supplier_id):
#     supplier_commodities = SupplierCommodity.objects.filter(supplier_id=supplier_id)
    
#     response = {}

#     for sc in supplier_commodities:
#         orders = Order.objects.filter(
#             supplier_commodity_id=sc.id, status='accepted'
#         ).order_by('ordered_at')

#         if orders.count() < 2:
#             response[sc.commodity.name] = "Not enough data"
#             continue

#         df = pd.DataFrame(list(orders.values('ordered_at', 'quantity_requested')))
#         df['ds'] = pd.to_datetime(df['ordered_at']).dt.tz_localize(None)
#         df = df.groupby('ds')['quantity_requested'].sum().reset_index()
#         df.rename(columns={'quantity_requested': 'y'}, inplace=True)
    
#         logger.info(f"DataFrame for commodity {sc.commodity.name}:\n{df}")

#         model = Prophet()
#         model.fit(df)

#         future = model.make_future_dataframe(periods=7)
#         forecast = model.predict(future)

#         result = forecast[['ds', 'yhat']].tail(7)
#         response[sc.commodity.name] = result.to_dict(orient='records')

#     return JsonResponse(response, safe=False)


from prophet import Prophet
from django.http import JsonResponse
from inventory.models import Order, SupplierCommodity
import pandas as pd

def forecast_demand(request, supplier_id):
    supplier_commodities = SupplierCommodity.objects.filter(supplier_id=supplier_id)
    
    response = {}

    for sc in supplier_commodities:
        orders = Order.objects.filter(
            supplier_commodity_id=sc.id, status='accepted'
        ).order_by('ordered_at')

        if orders.count() < 2:
            response[sc.commodity.name] = "Not enough data"
            continue

        df = pd.DataFrame(list(orders.values('ordered_at', 'quantity_requested')))
        df['ds'] = pd.to_datetime(df['ordered_at']).dt.tz_localize(None)
        df = df.groupby('ds')['quantity_requested'].sum().reset_index()
        df.rename(columns={'quantity_requested': 'y'}, inplace=True)

        model = Prophet()
        model.fit(df)

        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)

        result = forecast[['ds', 'yhat']].tail(7)
        response[sc.commodity.name] = result.to_dict(orient='records')

    return JsonResponse(response, safe=False)
