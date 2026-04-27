"""Tests for the shared RAG backend selector."""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import ANY, Mock, patch

from app._shared_path import ensure_shared_backend_path

ensure_shared_backend_path()

from bookstore_shared.rag_backend import LocalRAGService, RemoteRAGService, build_rag_backend


class TestRAGBackend(unittest.TestCase):
    def test_builds_remote_backend_when_url_is_configured(self) -> None:
        with patch.dict(os.environ, {"RAG_SERVICE_URL": "http://rag:8000"}, clear=False):
            backend = build_rag_backend()

        self.assertIsInstance(backend, RemoteRAGService)
        self.assertEqual(backend.base_url, "http://rag:8000")

    @patch("bookstore_shared.rag_backend.request.urlopen")
    def test_remote_backend_posts_json_and_forwards_authorization(
        self,
        mock_urlopen: Mock,
    ) -> None:
        response = Mock()
        response.read.return_value = json.dumps({"message": "ok"}).encode("utf-8")
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=None)
        response.status = 200
        mock_urlopen.return_value = response

        backend = RemoteRAGService(base_url="http://rag:8000")
        result = backend.get_book_recommendations(
            user_input="适合入门的 Python 书单",
            limit=5,
            authorization="Bearer test-token",
        )

        self.assertEqual(result, {"message": "ok"})
        request_obj = mock_urlopen.call_args.args[0]
        self.assertEqual(request_obj.full_url, "http://rag:8000/smart/recommendation")
        self.assertEqual(request_obj.get_header("Authorization"), "Bearer test-token")

    def test_local_backend_wraps_service(self) -> None:
        service = Mock()
        service.get_book_recommendations.return_value = {"message": "local"}

        backend = LocalRAGService(service=service)
        result = backend.get_book_recommendations(
            user_input="Python",
            db=Mock(),
            limit=7,
            authorization="Bearer ignored",
        )

        self.assertEqual(result, {"message": "local"})
        service.get_book_recommendations.assert_called_once_with(
            user_input="Python",
            db=ANY,
            limit=7,
        )


if __name__ == "__main__":
    unittest.main()
