"""Enqueue a single paper-position monitor job (cron / docker loop)."""

from __future__ import annotations

import logging

from rq import Queue

from app.core.redis import get_redis_connection
from app.tasks.position_monitor import run_position_monitor_cycle

logger = logging.getLogger(__name__)


def main() -> None:
    q = Queue(connection=get_redis_connection())
    job = q.enqueue(run_position_monitor_cycle)
    logger.info("Enqueued paper position monitor job id=%s", job.id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
