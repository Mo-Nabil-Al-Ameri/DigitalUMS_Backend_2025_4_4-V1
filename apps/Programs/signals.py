from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Program, ProgramLevel

@receiver(post_save, sender=Program)
def create_academic_levels(sender, instance, created, **kwargs):
    if created:
        for year in range(1, instance.duration_years + 1):
            ProgramLevel.objects.create(
                program=instance,
                level_number=year,
                description=f"Level {year} of {instance.name}"
            )
