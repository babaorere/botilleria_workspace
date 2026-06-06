import uuid
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

from models.message import Message
from repositories.message_repository import MessageRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: Session, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.repo = MessageRepository(db)

    def get_basic_metrics(self) -> dict:
        """Returns basic metrics for the tenant's interactions."""
        # 1. Total conversations
        # Count unique conversation_ids for this tenant in messages table
        total_convos = (
            self.db.query(func.count(func.distinct(Message.conversation_id)))
            .filter(Message.tenant_id == self.tenant_id)
            .scalar()
        ) or 0

        # 2. Total messages today
        today = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        messages_today = (
            self.db.query(func.count(Message.id))
            .filter(Message.tenant_id == self.tenant_id)
            .filter(Message.created_at >= today)
            .scalar()
        ) or 0

        # 3. Total messages all time
        total_messages = (
            self.db.query(func.count(Message.id))
            .filter(Message.tenant_id == self.tenant_id)
            .scalar()
        ) or 0

        # 4. DAU (Daily Active Users) - Users with messages in the last 24h
        # But wait, user ID is not directly in the messages table, it's in the conversations table,
        # or we can count distinct conversation_id for simplicity (Active Conversations Today)
        active_conversations_today = (
            self.db.query(func.count(func.distinct(Message.conversation_id)))
            .filter(Message.tenant_id == self.tenant_id)
            .filter(
                Message.created_at >= datetime.now(timezone.utc) - timedelta(days=1)
            )
            .scalar()
        ) or 0

        # 5. Average messages per conversation
        avg_messages_per_conv = 0.0
        if total_convos > 0:
            avg_messages_per_conv = round(total_messages / total_convos, 2)

        # 6. Most active hour (simplistic calculation based on all-time data)
        # Using EXTRACT(HOUR FROM created_at)
        active_hour_row = (
            self.db.query(
                func.extract("hour", Message.created_at).label("hour"),
                func.count(Message.id).label("count"),
            )
            .filter(Message.tenant_id == self.tenant_id)
            .group_by("hour")
            .order_by(func.count(Message.id).desc())
            .first()
        )

        peak_hour = None
        if active_hour_row:
            h = int(active_hour_row.hour)
            peak_hour = f"{h:02d}:00 - {h + 1:02d}:00"

        # 7. Response Time & Customer Satisfaction (SLA < 2000ms)
        avg_response_time = (
            self.db.query(func.avg(Message.response_time_ms))
            .filter(Message.tenant_id == self.tenant_id)
            .filter(Message.response_time_ms.isnot(None))
            .scalar()
        ) or 0.0

        fast_responses_count = (
            self.db.query(func.count(Message.id))
            .filter(Message.tenant_id == self.tenant_id)
            .filter(Message.response_time_ms <= 2000)
            .scalar()
        ) or 0

        total_assistant_messages = (
            self.db.query(func.count(Message.id))
            .filter(Message.tenant_id == self.tenant_id)
            .filter(Message.role == "assistant")
            .scalar()
        ) or 0

        fast_responses_percentage = 0.0
        if total_assistant_messages > 0:
            fast_responses_percentage = round(
                (fast_responses_count / total_assistant_messages) * 100, 2
            )

        # 8. Conversation Duration (Min, Max, Avg) in seconds
        # Calculate MAX(created_at) - MIN(created_at) per conversation
        durations_subquery = (
            self.db.query(
                Message.conversation_id,
                func.extract(
                    "epoch", func.max(Message.created_at) - func.min(Message.created_at)
                ).label("duration_sec"),
            )
            .filter(Message.tenant_id == self.tenant_id)
            .group_by(Message.conversation_id)
            .having(
                func.count(Message.id) > 1
            )  # Only conversations with at least 2 messages
            .subquery()
        )

        duration_stats = self.db.query(
            func.min(durations_subquery.c.duration_sec).label("min_duration"),
            func.max(durations_subquery.c.duration_sec).label("max_duration"),
            func.avg(durations_subquery.c.duration_sec).label("avg_duration"),
        ).first()

        min_duration = (
            round(duration_stats.min_duration or 0.0, 2) if duration_stats else 0.0
        )
        max_duration = (
            round(duration_stats.max_duration or 0.0, 2) if duration_stats else 0.0
        )
        avg_duration = (
            round(duration_stats.avg_duration or 0.0, 2) if duration_stats else 0.0
        )

        return {
            "total_conversations": total_convos,
            "messages_today": messages_today,
            "total_messages": total_messages,
            "active_conversations_24h": active_conversations_today,
            "avg_messages_per_conversation": avg_messages_per_conv,
            "peak_activity_hour": peak_hour or "N/A",
            "avg_response_time_ms": round(avg_response_time, 2),
            "fast_responses_percentage": fast_responses_percentage,
            "conversation_duration_sec": {
                "min": min_duration,
                "max": max_duration,
                "avg": avg_duration,
            },
        }
