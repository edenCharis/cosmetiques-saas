from django.db import models
from core.tenancy import get_current_tenant

class TenantAwareManager(models.Manager):

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()

        if tenant is None:
            return qs.none()  # 🔒 sécurité MAX

        return qs.filter(tenant=tenant)
