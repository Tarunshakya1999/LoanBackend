from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Customer, Transaction, ShopkeeperProfile


# ── Subscription Admin ────────────────────────────────────────────────────────

@admin.register(ShopkeeperProfile)
class ShopkeeperProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'shop_name', 'upi_id',
        'plan_badge', 'access_status_badge',
        'trial_days_left', 'subscription_end',
        'is_manually_blocked',
    ]
    list_filter  = ['plan', 'is_manually_blocked']
    search_fields = ['user__username', 'shop_name', 'upi_id']
    readonly_fields = ['trial_start', 'access_status_badge', 'trial_days_left']

    actions = [
        'action_activate_monthly',
        'action_activate_yearly',
        'action_block_users',
        'action_unblock_users',
        'action_reset_trial',
    ]

    fieldsets = (
        ('User Info', {
            'fields': ('user', 'shop_name', 'upi_id')
        }),
        ('Subscription', {
            'fields': ('plan', 'trial_start', 'subscription_end', 'is_manually_blocked'),
            'description': '⚠️ Plan change karne ke baad "Save" dabao. Monthly/Yearly activate karne ke liye Actions use karo.'
        }),
        ('Status (Read Only)', {
            'fields': ('access_status_badge', 'trial_days_left'),
        }),
    )

    def plan_badge(self, obj):
        colors = {
            'free_trial': '#f59e0b',
            'monthly':    '#3b82f6',
            'yearly':     '#8b5cf6',
            'blocked':    '#ef4444',
        }
        color = colors.get(obj.plan, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700">{}</span>',
            color, obj.get_plan_display()
        )
    plan_badge.short_description = 'Plan'

    def access_status_badge(self, obj):
        status = obj.access_status
        config = {
            'trial':               ('#10b981', '✅ Trial Active'),
            'active':              ('#3b82f6', '✅ Subscribed'),
            'trial_expired':       ('#ef4444', '⛔ Trial Expired'),
            'subscription_expired':('#ef4444', '⛔ Sub. Expired'),
            'blocked':             ('#7f1d1d', '🚫 BLOCKED'),
        }
        color, label = config.get(status, ('#6b7280', status))
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700">{}</span>',
            color, label
        )
    access_status_badge.short_description = 'Access Status'

    def trial_days_left(self, obj):
        days = obj.trial_days_remaining
        if obj.plan != 'free_trial':
            return '-'
        if days > 0:
            return format_html('<span style="color:#10b981;font-weight:700">{} days</span>', days)
        return format_html('<span style="color:#ef4444;font-weight:700">Expired</span>')
    trial_days_left.short_description = 'Trial Left'

    # ── Bulk actions ──────────────────────────────────────────────────────────

    @admin.action(description='✅ Activate Monthly (₹399) for selected')
    def action_activate_monthly(self, request, queryset):
        for profile in queryset:
            profile.activate_monthly()
        self.message_user(request, f'{queryset.count()} users ko Monthly plan activate kiya gaya.')

    @admin.action(description='⭐ Activate Yearly (₹4999) for selected')
    def action_activate_yearly(self, request, queryset):
        for profile in queryset:
            profile.activate_yearly()
        self.message_user(request, f'{queryset.count()} users ko Yearly plan activate kiya gaya.')

    @admin.action(description='🚫 Block selected users')
    def action_block_users(self, request, queryset):
        queryset.update(is_manually_blocked=True)
        self.message_user(request, f'{queryset.count()} users block kiye gaye.')

    @admin.action(description='✅ Unblock selected users')
    def action_unblock_users(self, request, queryset):
        queryset.update(is_manually_blocked=False)
        self.message_user(request, f'{queryset.count()} users unblock kiye gaye.')

    @admin.action(description='🔄 Reset 7-day trial for selected')
    def action_reset_trial(self, request, queryset):
        queryset.update(
            plan='free_trial',
            trial_start=timezone.now(),
            subscription_end=None,
            is_manually_blocked=False,
        )
        self.message_user(request, f'{queryset.count()} users ka trial reset kiya gaya.')


# ── Customer & Transaction Admin ──────────────────────────────────────────────

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display  = ['name', 'phone', 'owner', 'balance', 'created_at']
    list_filter   = ['owner']
    search_fields = ['name', 'phone']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = ['customer', 'transaction_type', 'amount', 'date', 'note']
    list_filter   = ['transaction_type', 'date']
    search_fields = ['customer__name', 'note']