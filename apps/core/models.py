from django.db import models


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class SoftDeleteModel(models.Model):
    is_deleted  = models.BooleanField(default=False)
    deleted_at  = models.DateTimeField(null=True, blank=True)

    objects     = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()