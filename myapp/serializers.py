from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Customer, Transaction, ShopkeeperProfile


# ── Auth Serializers ───────────────────────────────────────────────────────────

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email']    = user.email
        try:
            p = user.profile
            token['upi_id']       = p.upi_id    or ''
            token['shop_name']    = p.shop_name or ''
            token['access_status']= p.access_status
            token['trial_days']   = p.trial_days_remaining
            token['plan']         = p.plan
        except Exception:
            token['upi_id']        = ''
            token['shop_name']     = ''
            token['access_status'] = 'blocked'
            token['trial_days']    = 0
            token['plan']          = 'blocked'
        return token


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, label='Confirm Password')
    upi_id    = serializers.CharField(required=False, allow_blank=True, max_length=100)
    shop_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    class Meta:
        model  = User
        fields = ['username', 'email', 'password', 'password2', 'upi_id', 'shop_name']

    def validate_upi_id(self, value):
        if value and '@' not in value:
            raise serializers.ValidationError('Valid UPI ID daalo (e.g. name@upi)')
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        upi_id    = validated_data.pop('upi_id', '')
        shop_name = validated_data.pop('shop_name', '')
        validated_data.pop('password2')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        # Signal ne profile bana di hogi, bas update karo
        user.profile.upi_id    = upi_id
        user.profile.shop_name = shop_name
        user.profile.save()
        return user


# ── Profile Serializer ─────────────────────────────────────────────────────────

class ProfileSerializer(serializers.ModelSerializer):
    access_status     = serializers.ReadOnlyField()
    trial_days_remaining = serializers.ReadOnlyField()
    has_active_access = serializers.ReadOnlyField()
    trial_expires_at  = serializers.ReadOnlyField()

    class Meta:
        model  = ShopkeeperProfile
        fields = [
            'upi_id', 'shop_name',
            'plan', 'trial_start', 'subscription_end',
            'access_status', 'trial_days_remaining',
            'has_active_access', 'trial_expires_at',
        ]
        read_only_fields = ['plan', 'trial_start', 'subscription_end']


# ── Transaction Serializer ─────────────────────────────────────────────────────

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model        = Transaction
        fields       = ['id', 'customer', 'transaction_type', 'amount', 'note', 'date', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than 0.')
        return value


# ── Customer Serializers ───────────────────────────────────────────────────────

class CustomerSerializer(serializers.ModelSerializer):
    balance       = serializers.ReadOnlyField()
    total_udhaar  = serializers.ReadOnlyField()
    total_payment = serializers.ReadOnlyField()

    class Meta:
        model        = Customer
        fields       = ['id', 'name', 'phone', 'balance', 'total_udhaar', 'total_payment', 'created_at']
        read_only_fields = ['id', 'created_at']


class CustomerDetailSerializer(serializers.ModelSerializer):
    transactions  = TransactionSerializer(many=True, read_only=True)
    balance       = serializers.ReadOnlyField()
    total_udhaar  = serializers.ReadOnlyField()
    total_payment = serializers.ReadOnlyField()

    class Meta:
        model        = Customer
        fields       = ['id', 'name', 'phone', 'balance', 'total_udhaar', 'total_payment', 'created_at', 'transactions']
        read_only_fields = ['id', 'created_at']