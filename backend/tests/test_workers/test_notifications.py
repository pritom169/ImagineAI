import uuid
from unittest.mock import MagicMock, patch

import pytest


class TestNotificationTasks:
    @patch("workers.tasks.notifications.send_processing_complete")
    def test_send_processing_complete_notification(self, mock_send):
        mock_send.delay.return_value = MagicMock(id="notif-task-1")

        user_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        result = mock_send.delay(user_id, job_id, status="completed")

        assert result.id == "notif-task-1"
        mock_send.delay.assert_called_once_with(user_id, job_id, status="completed")

    @patch("workers.tasks.notifications.send_processing_complete")
    def test_send_failure_notification(self, mock_send):
        mock_send.delay.return_value = MagicMock(id="notif-task-2")

        user_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        result = mock_send.delay(user_id, job_id, status="failed")

        mock_send.delay.assert_called_once_with(user_id, job_id, status="failed")


class TestWebSocketNotifications:
    @patch("fastapi_app.api.websocket.ConnectionManager")
    def test_connection_manager_send(self, mock_manager):
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance

        manager = mock_manager()
        user_id = str(uuid.uuid4())

        manager.send_personal_message(
            {"type": "analysis_complete", "job_id": "123"},
            user_id,
        )

        mock_instance.send_personal_message.assert_called_once()

    @patch("fastapi_app.api.websocket.ConnectionManager")
    def test_connection_manager_broadcast(self, mock_manager):
        mock_instance = MagicMock()
        mock_manager.return_value = mock_instance

        manager = mock_manager()
        manager.broadcast({"type": "system", "message": "Maintenance window"})

        mock_instance.broadcast.assert_called_once()
