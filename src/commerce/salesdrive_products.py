"""Sync каталогу → SalesDrive (/product-handler/): назва, sku, ціна, залишок."""
from __future__ import annotations

import logging
from collections.abc import Iterable

from django.db import transaction

from src.commerce import salesdrive_client as client
from src.commerce import salesdrive_mapper as mapper
from src.catalog.models import ProductVariant

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


def sync_variants(variants: Iterable[ProductVariant]) -> dict:
    """Upsert список варіантів. Повертає counters."""
    items = [v for v in variants if getattr(v, "sku", None)]
    if not items:
        return {"synced": 0, "batches": 0, "skipped": True, "reason": "empty"}
    if not client.is_configured():
        logger.warning("SalesDrive products: немає API URL/KEY — sync пропущено")
        return {"synced": 0, "batches": 0, "skipped": True, "reason": "not_configured"}

    synced = batches = 0
    for i in range(0, len(items), BATCH_SIZE):
        chunk = items[i : i + BATCH_SIZE]
        payload = [mapper.build_product_payload(v) for v in chunk]
        client.upsert_products(payload)
        synced += len(chunk)
        batches += 1
    return {"synced": synced, "batches": batches, "skipped": False}


def sync_variant_ids(variant_ids: list[int]) -> dict:
    qs = ProductVariant.objects.filter(pk__in=variant_ids).select_related("product")
    return sync_variants(list(qs))


def schedule_sync_variant_ids(variant_ids: list[int]) -> None:
    """Після коміту транзакції адмінки — щоб не блокувати save."""
    ids = [int(x) for x in variant_ids if x]

    def _run() -> None:
        try:
            result = sync_variant_ids(ids)
            logger.info("SalesDrive product sync: %s", result)
        except Exception:
            logger.exception("SalesDrive product sync failed for ids=%s", ids)

    if ids:
        transaction.on_commit(_run)


def sync_all_variants(*, limit: int | None = None) -> dict:
    qs = ProductVariant.objects.select_related("product").order_by("pk")
    if limit:
        qs = qs[:limit]
    return sync_variants(list(qs))
