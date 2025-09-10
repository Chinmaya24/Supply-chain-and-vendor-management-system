from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken

# Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = [
        ('supplier', 'Supplier'),
        ('vendor', 'Vendor'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    pincode = models.CharField(max_length=10)
    state = models.CharField(max_length=50)

    # Avoid conflicts with auth.Group and auth.Permission
    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)



# Commodity Model (Stores commodity types)
class ListCommodity(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# Supplier's Inventory (Intermediary Table)
class SupplierCommodity(models.Model):
    supplier = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'supplier'})
    commodity = models.ForeignKey(ListCommodity, on_delete=models.CASCADE)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    manufactured_company = models.CharField(max_length=100)
    available_units = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.commodity.name} - {self.supplier.username} ({self.available_units} units)"


# Order Model (Vendor buys from Supplier)
class Order(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'vendor'})
    supplier_commodity = models.ForeignKey(SupplierCommodity, on_delete=models.CASCADE)
    quantity_requested = models.PositiveIntegerField()
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    ordered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.vendor.username} -> {self.supplier_commodity.commodity.name}"

    def accept_order(self):
        """When supplier accepts the order, decrease stock."""
        if self.quantity_requested <= self.supplier_commodity.available_units:
            self.supplier_commodity.available_units -= self.quantity_requested
            self.supplier_commodity.save()
            self.status = 'accepted'
            self.save()

    def reject_order(self):
        """Supplier can reject an order."""
        self.status = 'rejected'
        self.save()


# Rating Model
class Rating(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='rating')
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'vendor'}, related_name='vendor_ratings')
    supplier = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'supplier'}, related_name='supplier_ratings')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating for Order {self.order.id} - {self.rating} stars"

    class Meta:
        unique_together = ('order', 'vendor')  # One rating per order


