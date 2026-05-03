# from django.contrib.auth.models import User
# from rest_framework import generics, status
# from rest_framework.permissions import AllowAny, IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework_simplejwt.views import TokenObtainPairView
# from rest_framework.exceptions import PermissionDenied

# from .models import Customer, Transaction
# from .serializers import (
#     MyTokenObtainPairSerializer,
#     RegisterSerializer,
#     ProfileSerializer,
#     CustomerSerializer,
#     CustomerDetailSerializer,
#     TransactionSerializer,
# )


# # ── Subscription check mixin ───────────────────────────────────────────────────
# # Har protected view mein ye mixin lagao — access check automatic ho jayega

# class SubscriptionRequiredMixin:
#     """
#     Is mixin ko use karne wali views check karengi ki user ka subscription active hai ya nahi.
#     Agar nahi hai toh 403 + subscription info dega.
#     """
#     def check_subscription(self, request):
#         try:
#             profile = request.user.profile
#         except Exception:
#             raise PermissionDenied({'error': 'subscription_required', 'message': 'Profile nahi mili.'})

#         if not profile.has_active_access:
#             raise PermissionDenied({
#                 'error':         'subscription_required',
#                 'access_status': profile.access_status,
#                 'plan':          profile.plan,
#                 'message':       self._get_block_message(profile.access_status),
#             })

#     def _get_block_message(self, status):
#         messages = {
#             'trial_expired':        '7 din ka free trial khatam ho gaya. Please subscribe karo.',
#             'subscription_expired': 'Aapka subscription expire ho gaya hai. Please renew karo.',
#             'blocked':              'Aapka account block kar diya gaya hai. Admin se contact karo.',
#         }
#         return messages.get(status, 'Access nahi hai.')

#     def initial(self, request, *args, **kwargs):
#         super().initial(request, *args, **kwargs)
#         if request.user and request.user.is_authenticated:
#             self.check_subscription(request)


# # ── Auth Views ─────────────────────────────────────────────────────────────────

# class MyTokenObtainPairView(TokenObtainPairView):
#     serializer_class   = MyTokenObtainPairSerializer
#     permission_classes = [AllowAny]


# class RegisterView(generics.CreateAPIView):
#     queryset           = User.objects.all()
#     serializer_class   = RegisterSerializer
#     permission_classes = [AllowAny]

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.save()
#         p = user.profile
#         return Response(
#             {
#                 'message':      'Account created successfully. Please login.',
#                 'upi_id':       p.upi_id    or '',
#                 'shop_name':    p.shop_name or '',
#                 'plan':         p.plan,
#                 'trial_days':   p.trial_days_remaining,
#                 'access_status': p.access_status,
#             },
#             status=status.HTTP_201_CREATED
#         )


# # ── Profile View ───────────────────────────────────────────────────────────────

# class ProfileView(APIView):
#     """
#     GET  → subscription info + profile
#     PATCH → UPI ID / shop name update
#     No subscription check here — user blocked hone ke baad bhi profile dekh sake
#     """
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         p = request.user.profile
#         return Response({
#             'username':           request.user.username,
#             'email':              request.user.email,
#             'upi_id':             p.upi_id    or '',
#             'shop_name':          p.shop_name or '',
#             'plan':               p.plan,
#             'access_status':      p.access_status,
#             'trial_days_remaining': p.trial_days_remaining,
#             'trial_expires_at':   p.trial_expires_at,
#             'subscription_end':   p.subscription_end,
#             'has_active_access':  p.has_active_access,
#         })

#     def patch(self, request):
#         p = request.user.profile
#         serializer = ProfileSerializer(p, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         # Only allow upi_id and shop_name updates
#         p.upi_id    = request.data.get('upi_id',    p.upi_id)
#         p.shop_name = request.data.get('shop_name', p.shop_name)
#         p.save()
#         return Response({
#             'message':   'Profile updated.',
#             'upi_id':    p.upi_id    or '',
#             'shop_name': p.shop_name or '',
#         })


# # ── Dashboard ──────────────────────────────────────────────────────────────────

# class DashboardView(SubscriptionRequiredMixin, APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         customers = Customer.objects.filter(owner=request.user)

#         total_udhaar      = sum(c.total_udhaar  for c in customers)
#         total_payment     = sum(c.total_payment for c in customers)
#         total_outstanding = total_udhaar - total_payment

#         customer_balances = sorted(
#             [{'id': c.id, 'name': c.name, 'phone': c.phone, 'balance': c.balance} for c in customers],
#             key=lambda x: x['balance'], reverse=True
#         )

#         customer_ids = customers.values_list('id', flat=True)
#         recent_txns  = Transaction.objects.filter(
#             customer_id__in=customer_ids
#         ).select_related('customer').order_by('-date', '-created_at')[:10]

#         recent_data = [
#             {
#                 'id':               txn.id,
#                 'customer_name':    txn.customer.name,
#                 'customer_id':      txn.customer.id,
#                 'transaction_type': txn.transaction_type,
#                 'amount':           str(txn.amount),
#                 'note':             txn.note,
#                 'date':             txn.date,
#             }
#             for txn in recent_txns
#         ]

#         p = request.user.profile
#         return Response({
#             'total_outstanding':      total_outstanding,
#             'total_udhaar':           total_udhaar,
#             'total_payment':          total_payment,
#             'total_customers':        customers.count(),
#             'customers_with_balance': sum(1 for c in customer_balances if c['balance'] > 0),
#             'customer_balances':      customer_balances,
#             'recent_transactions':    recent_data,
#             'shopkeeper_upi':         p.upi_id    or '',
#             'shop_name':              p.shop_name or '',
#             # Subscription info
#             'access_status':          p.access_status,
#             'trial_days_remaining':   p.trial_days_remaining,
#             'plan':                   p.plan,
#         })


# # ── Customer Views ─────────────────────────────────────────────────────────────

# class CustomerListCreateView(SubscriptionRequiredMixin, generics.ListCreateAPIView):
#     serializer_class   = CustomerSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Customer.objects.filter(owner=self.request.user)

#     def perform_create(self, serializer):
#         serializer.save(owner=self.request.user)


# class CustomerDetailView(SubscriptionRequiredMixin, generics.RetrieveDestroyAPIView):
#     serializer_class   = CustomerDetailSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Customer.objects.filter(owner=self.request.user)


# # ── Transaction Views ──────────────────────────────────────────────────────────

# class TransactionListCreateView(SubscriptionRequiredMixin, generics.ListCreateAPIView):
#     serializer_class   = TransactionSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Transaction.objects.filter(
#             customer_id=self.kwargs.get('customer_id'),
#             customer__owner=self.request.user
#         )

#     def perform_create(self, serializer):
#         customer_id = self.kwargs.get('customer_id')
#         try:
#             customer = Customer.objects.get(id=customer_id, owner=self.request.user)
#         except Customer.DoesNotExist:
#             raise PermissionDenied('Customer not found.')
#         serializer.save(customer=customer)


# class TransactionDeleteView(SubscriptionRequiredMixin, generics.DestroyAPIView):
#     serializer_class   = TransactionSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Transaction.objects.filter(customer__owner=self.request.user)



"New Views.py Code"

from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import PermissionDenied

from .models import Customer, Transaction
from .serializers import (
    MyTokenObtainPairSerializer,
    RegisterSerializer,
    ProfileSerializer,
    CustomerSerializer,
    CustomerDetailSerializer,
    TransactionSerializer,
)


# ─────────────────────────────────────────────────────────────────────────────
# Custom Exception — DRF ka PermissionDenied dict ko string bana deta hai
# isliye apna exception banaya jisse dispatch() pakad ke proper JSON dega
# ─────────────────────────────────────────────────────────────────────────────

class SubscriptionExpiredException(Exception):
    def __init__(self, access_status, plan, message):
        self.access_status = access_status
        self.plan          = plan
        self.message       = message
        super().__init__(message)


# ─────────────────────────────────────────────────────────────────────────────
# Subscription Required Mixin
# Isko har protected view mein lagao — trial/subscription check automatic hoga
# ─────────────────────────────────────────────────────────────────────────────

class SubscriptionRequiredMixin:
    """
    Views jo is mixin ko use karti hain — unhe check hoga ki user ka
    trial ya subscription active hai ya nahi.

    Block hone pe frontend ko milega:
    {
        "error": "subscription_required",
        "access_status": "trial_expired",   <-- frontend yahi check karta hai
        "plan": "free_trial",
        "message": "..."
    }
    HTTP Status: 403
    """

    BLOCK_MESSAGES = {
        'trial_expired':        '7 din ka free trial khatam ho gaya. Subscribe karo.',
        'subscription_expired': 'Aapka subscription expire ho gaya. Renew karo.',
        'blocked':              'Account block hai. Admin se contact karo.',
    }

    def check_subscription(self, request):
        try:
            profile = request.user.profile
        except Exception:
            raise SubscriptionExpiredException(
                access_status='blocked',
                plan='blocked',
                message='Profile nahi mili. Admin se contact karo.'
            )

        if not profile.has_active_access:
            raise SubscriptionExpiredException(
                access_status=profile.access_status,
                plan=profile.plan,
                message=self.BLOCK_MESSAGES.get(
                    profile.access_status, 'Access nahi hai.'
                )
            )

    def dispatch(self, request, *args, **kwargs):
        """
        SubscriptionExpiredException ko pakad ke proper JSON 403 return karta hai.
        Yahi fix hai — bina iske DRF dict ko string bana deta tha.
        """
        try:
            return super().dispatch(request, *args, **kwargs)
        except SubscriptionExpiredException as e:
            return Response(
                {
                    'error':         'subscription_required',
                    'access_status': e.access_status,
                    'plan':          e.plan,
                    'message':       e.message,
                },
                status=status.HTTP_403_FORBIDDEN
            )

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user and request.user.is_authenticated:
            self.check_subscription(request)


# ─────────────────────────────────────────────────────────────────────────────
# Auth Views
# ─────────────────────────────────────────────────────────────────────────────

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class   = MyTokenObtainPairSerializer
    permission_classes = [AllowAny]


class RegisterView(generics.CreateAPIView):
    queryset           = User.objects.all()
    serializer_class   = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        p    = user.profile
        return Response(
            {
                'message':       'Account created successfully. Please login.',
                'upi_id':        p.upi_id    or '',
                'shop_name':     p.shop_name or '',
                'plan':          p.plan,
                'trial_days':    p.trial_days_remaining,
                'access_status': p.access_status,
            },
            status=status.HTTP_201_CREATED
        )


# ─────────────────────────────────────────────────────────────────────────────
# Profile View — Subscription check NAHI hai
# Blocked user bhi apna profile dekh sake aur payment info le sake
# ─────────────────────────────────────────────────────────────────────────────

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        p = request.user.profile
        return Response({
            'username':              request.user.username,
            'email':                 request.user.email,
            'upi_id':                p.upi_id    or '',
            'shop_name':             p.shop_name or '',
            'plan':                  p.plan,
            'access_status':         p.access_status,
            'trial_days_remaining':  p.trial_days_remaining,
            'trial_expires_at':      p.trial_expires_at,
            'subscription_end':      p.subscription_end,
            'has_active_access':     p.has_active_access,
        })

    def patch(self, request):
        p = request.user.profile
        p.upi_id    = request.data.get('upi_id',    p.upi_id)
        p.shop_name = request.data.get('shop_name', p.shop_name)
        p.save()
        return Response({
            'message':   'Profile updated.',
            'upi_id':    p.upi_id    or '',
            'shop_name': p.shop_name or '',
        })


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard View
# ─────────────────────────────────────────────────────────────────────────────

class DashboardView(SubscriptionRequiredMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customers = Customer.objects.filter(owner=request.user)

        total_udhaar      = sum(c.total_udhaar  for c in customers)
        total_payment     = sum(c.total_payment for c in customers)
        total_outstanding = total_udhaar - total_payment

        customer_balances = sorted(
            [
                {
                    'id':      c.id,
                    'name':    c.name,
                    'phone':   c.phone,
                    'balance': c.balance,
                }
                for c in customers
            ],
            key=lambda x: x['balance'],
            reverse=True
        )

        customer_ids = customers.values_list('id', flat=True)
        recent_txns  = (
            Transaction.objects
            .filter(customer_id__in=customer_ids)
            .select_related('customer')
            .order_by('-date', '-created_at')[:10]
        )

        recent_data = [
            {
                'id':               txn.id,
                'customer_name':    txn.customer.name,
                'customer_id':      txn.customer.id,
                'transaction_type': txn.transaction_type,
                'amount':           str(txn.amount),
                'note':             txn.note,
                'date':             txn.date,
            }
            for txn in recent_txns
        ]

        p = request.user.profile
        return Response({
            'total_outstanding':      total_outstanding,
            'total_udhaar':           total_udhaar,
            'total_payment':          total_payment,
            'total_customers':        customers.count(),
            'customers_with_balance': sum(1 for c in customer_balances if c['balance'] > 0),
            'customer_balances':      customer_balances,
            'recent_transactions':    recent_data,
            'shopkeeper_upi':         p.upi_id    or '',
            'shop_name':              p.shop_name or '',
            'access_status':          p.access_status,
            'trial_days_remaining':   p.trial_days_remaining,
            'plan':                   p.plan,
        })


# ─────────────────────────────────────────────────────────────────────────────
# Customer Views
# ─────────────────────────────────────────────────────────────────────────────

class CustomerListCreateView(SubscriptionRequiredMixin, generics.ListCreateAPIView):
    serializer_class   = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Customer.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CustomerDetailView(SubscriptionRequiredMixin, generics.RetrieveDestroyAPIView):
    serializer_class   = CustomerDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Customer.objects.filter(owner=self.request.user)


# ─────────────────────────────────────────────────────────────────────────────
# Transaction Views
# ─────────────────────────────────────────────────────────────────────────────

class TransactionListCreateView(SubscriptionRequiredMixin, generics.ListCreateAPIView):
    serializer_class   = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(
            customer_id=self.kwargs.get('customer_id'),
            customer__owner=self.request.user
        )

    def perform_create(self, serializer):
        customer_id = self.kwargs.get('customer_id')
        try:
            customer = Customer.objects.get(
                id=customer_id,
                owner=self.request.user
            )
        except Customer.DoesNotExist:
            raise PermissionDenied('Customer not found.')
        serializer.save(customer=customer)


class TransactionDeleteView(SubscriptionRequiredMixin, generics.DestroyAPIView):
    serializer_class   = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(
            customer__owner=self.request.user
        )