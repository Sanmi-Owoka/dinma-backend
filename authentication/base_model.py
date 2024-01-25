import uuid

from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4(), editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_by_id(cls, obj_id: str) -> dict:
        try:
            queryset = cls.objects.get(id=obj_id)
            return {"status": True, "data": queryset}
        except cls.DoesNotExist:
            return {"status": False, "data": None}

    @classmethod
    def get_by_user_id(cls, user_) -> dict:
        try:
            queryset = cls.objects.get(user=user_)
            return {"status": True, "data": queryset}
        except cls.DoesNotExist:
            return {"status": False, "data": None}

    class Meta:
        abstract = True
        ordering = ("-created_at",)
