"""Session tracker — счётчик concurrent users (in-memory)"""
from datetime import datetime, timezone, timedelta
from typing import Dict
from structlog import get_logger

log = get_logger()


class SessionTracker:
    """Отслеживает активные сессии пользователей (in-memory)"""

    def __init__(self, timeout_seconds: int = 1800):  # 30 минут
        """
        Args:
            timeout_seconds: Таймаут неактивности (секунды)
        """
        self.timeout_seconds = timeout_seconds
        self._sessions: Dict[str, datetime] = {}  # session_id → last_heartbeat

    def add(self, session_id: str):
        """Добавить сессию"""
        self._sessions[session_id] = datetime.now(timezone.utc)
        log.debug("Session added", session_id=session_id, active_count=len(self._sessions))

    def remove(self, session_id: str):
        """Удалить сессию"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            log.debug("Session removed", session_id=session_id, active_count=len(self._sessions))

    def heartbeat(self, session_id: str):
        """Обновить heartbeat сессии"""
        if session_id in self._sessions:
            self._sessions[session_id] = datetime.now(timezone.utc)

    def active_count(self) -> int:
        """Количество активных сессий (с учётом timeout)"""
        self._cleanup_expired()
        return len(self._sessions)

    def _cleanup_expired(self):
        """Удаляет сессии с истёкшим timeout"""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.timeout_seconds)

        expired = [sid for sid, last_seen in self._sessions.items() if last_seen < cutoff]
        for sid in expired:
            del self._sessions[sid]
            log.debug("Session expired", session_id=sid)

    def is_active(self, session_id: str) -> bool:
        """Проверяет активна ли сессия"""
        if session_id not in self._sessions:
            return False

        last_seen = self._sessions[session_id]
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.timeout_seconds)
        return last_seen >= cutoff
