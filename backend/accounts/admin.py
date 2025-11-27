from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	"""Custom UserAdmin to show rol and use email as identifier."""
	ordering = ("email",)
	list_display = ("email", "username", "rol", "is_staff", "is_active")
	list_filter = ("rol", "is_staff", "is_active")
	search_fields = ("email", "username")

	fieldsets = (
		(None, {"fields": ("email", "password")} ),
		(_("Personal info"), {"fields": ("username",)}),
		(_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "rol", "groups", "user_permissions")} ),
		(_("Important dates"), {"fields": ("last_login", "date_joined")}),
	)

	add_fieldsets = (
		(None, {
			"classes": ("wide",),
			"fields": ("email", "username", "rol", "password1", "password2"),
		}),
	)

	filter_horizontal = ("groups", "user_permissions")
