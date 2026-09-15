"""Backfill: конвертація існуючих ImageField у WebP.

Запуск:
  python3 manage.py convert_media_to_webp
  python3 manage.py convert_media_to_webp --dry-run
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.models import Q

from src.core.utils.images import (
    convert_imagefield_to_webp,
    image_needs_webp_processing,
    iter_webp_targets,
)


class Command(BaseCommand):
    help = "Конвертує існуючі зображення (крім логотипів) у WebP з ресайзом"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Лише показати, що буде змінено",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        converted = 0
        skipped = 0
        errors = 0

        for model, field_name, max_side in iter_webp_targets():
            qs = model.objects.exclude(
                Q(**{f"{field_name}__isnull": True}) | Q(**{field_name: ""})
            ).iterator()

            for obj in qs:
                field_file = getattr(obj, field_name)
                label = f"{model._meta.label}.{field_name} pk={obj.pk} ({field_file.name})"
                if not image_needs_webp_processing(field_file, max_side):
                    skipped += 1
                    continue
                if dry_run:
                    self.stdout.write(f"WOULD CONVERT  {label}")
                    converted += 1
                    continue
                try:
                    convert_imagefield_to_webp(obj, field_name, max_side=max_side)
                    obj._webp_converting = True
                    try:
                        obj.save(update_fields=[field_name])
                    finally:
                        obj._webp_converting = False
                    converted += 1
                    self.stdout.write(self.style.SUCCESS(f"OK  {label} → {getattr(obj, field_name).name}"))
                except Exception as exc:
                    errors += 1
                    self.stderr.write(self.style.ERROR(f"FAIL  {label}: {exc}"))

        self.stdout.write(
            f"\nГотово. converted={converted} skipped={skipped} errors={errors}"
            + (" (dry-run)" if dry_run else "")
        )
