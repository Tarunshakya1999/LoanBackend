from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta


class ShopkeeperProfile(models.Model):
    """Har User ke liye profile — UPI, Shop Name, aur Subscription info"""

    PLAN_FREE_TRIAL = 'free_trial'
    PLAN_MONTHLY    = 'monthly'
    PLAN_YEARLY     = 'yearly'
    PLAN_BLOCKED    = 'blocked'

    PLAN_CHOICES = [
        (PLAN_FREE_TRIAL, 'Free Trial (7 days)'),
        (PLAN_MONTHLY,    'Monthly (₹99/month)'),
        (PLAN_YEARLY,     'Yearly (₹999/year)'),
        (PLAN_BLOCKED,    'Blocked'),
    ]

    user      = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    upi_id    = models.CharField(max_length=100, blank=True, null=True)
    shop_name = models.CharField(max_length=150, blank=True, null=True)

    # ── Subscription fields ──
    plan            = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE_TRIAL)
    trial_start     = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)  # Monthly/Yearly expiry
    is_manually_blocked = models.BooleanField(default=False)        # Admin se manual block

    def __str__(self):
        return f"{self.user.username} [{self.plan}] — {self.upi_id or 'No UPI'}"

    # ── Core subscription logic ──────────────────────────────────────────────

    @property
    def is_trial_active(self):
        if self.plan != self.PLAN_FREE_TRIAL or not self.trial_start:
            return False
        return timezone.now() < self.trial_start + timedelta(days=7)

    @property
    def trial_days_remaining(self):
        if not self.is_trial_active:
            return 0
        remaining = (self.trial_start + timedelta(days=7)) - timezone.now()
        return max(0, remaining.days)

    @property
    def trial_expires_at(self):
        if self.trial_start:
            return self.trial_start + timedelta(days=7)
        return None

    @property
    def is_subscription_active(self):
        if self.plan in (self.PLAN_MONTHLY, self.PLAN_YEARLY):
            if self.subscription_end and timezone.now() < self.subscription_end:
                return True
        return False

    @property
    def has_active_access(self):
        """
        TRUE  → user app use kar sakta hai
        FALSE → access block karo
        """
        if self.is_manually_blocked:
            return False
        if self.plan == self.PLAN_BLOCKED:
            return False
        if self.is_trial_active:
            return True
        if self.is_subscription_active:
            return True
        return False

    @property
    def access_status(self):
        """Frontend ke liye detailed status string"""
        if self.is_manually_blocked or self.plan == self.PLAN_BLOCKED:
            return 'blocked'
        if self.is_trial_active:
            return 'trial'
        if self.is_subscription_active:
            return 'active'
        # Trial ya subscription dono khatam
        if self.plan == self.PLAN_FREE_TRIAL:
            return 'trial_expired'
        return 'subscription_expired'

    def activate_monthly(self):
        from datetime import timedelta
        self.plan = self.PLAN_MONTHLY
        self.subscription_end = timezone.now() + timedelta(days=30)
        self.is_manually_blocked = False
        self.save()

    def activate_yearly(self):
        from datetime import timedelta
        self.plan = self.PLAN_YEARLY
        self.subscription_end = timezone.now() + timedelta(days=365)
        self.is_manually_blocked = False
        self.save()

    def block_user(self):
        self.is_manually_blocked = True
        self.save()

    def unblock_user(self):
        self.is_manually_blocked = False
        self.save()


# ── Signals ──────────────────────────────────────────────────────────────────

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        ShopkeeperProfile.objects.create(
            user=instance,
            plan=ShopkeeperProfile.PLAN_FREE_TRIAL,
            trial_start=timezone.now(),
        )

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except ShopkeeperProfile.DoesNotExist:
        pass


# ── Customer & Transaction (same as before) ───────────────────────────────────

class Customer(models.Model):
    owner      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers')
    name       = models.CharField(max_length=100)
    phone      = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.owner.username})"

    @property
    def total_udhaar(self):
        from django.db.models import Sum
        result = self.transactions.filter(transaction_type='udhaar').aggregate(Sum('amount'))
        return result['amount__sum'] or 0

    @property
    def total_payment(self):
        from django.db.models import Sum
        result = self.transactions.filter(transaction_type='payment').aggregate(Sum('amount'))
        return result['amount__sum'] or 0

    @property
    def balance(self):
        return self.total_udhaar - self.total_payment


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('udhaar', 'Udhaar'),
        ('payment', 'Payment'),
    ]

    customer         = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount           = models.DecimalField(max_digits=10, decimal_places=2)
    note             = models.CharField(max_length=255, blank=True, null=True)
    date             = models.DateField()
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.transaction_type} - ₹{self.amount} ({self.customer.name})"