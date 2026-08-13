from django.db import models


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(owner_deleted=False, tenant_deleted=False)


class OwnerVisibleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(owner_deleted=False)


class TenantVisibleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(tenant_deleted=False)


class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class SoftDeleteModel(models.Model):
    owner_deleted = models.BooleanField(default=False)
    owner_deleted_at = models.DateTimeField(null=True, blank=True)
    tenant_deleted = models.BooleanField(default=False)
    tenant_deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()  # hides if EITHER side deleted
    owner_objects = OwnerVisibleManager()  # owner's view
    tenant_objects = TenantVisibleManager()  # tenant's view
    all_objects = AllObjectsManager()  # admin sees all

    class Meta:
        abstract = True

    def soft_delete_by_owner(self):
        from django.utils import timezone

        self.owner_deleted = True
        self.owner_deleted_at = timezone.now()
        self.save()

    def soft_delete_by_tenant(self):
        from django.utils import timezone

        self.tenant_deleted = True
        self.tenant_deleted_at = timezone.now()
        self.save()

    def restore_owner(self):
        self.owner_deleted = False
        self.owner_deleted_at = None
        self.save()

    def restore_tenant(self):
        self.tenant_deleted = False
        self.tenant_deleted_at = None
        self.save()
