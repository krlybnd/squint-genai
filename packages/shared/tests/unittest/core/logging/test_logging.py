import logging
import unittest

from agentic_shared.core.logging import APP_LOGGER_NAMES, setup_logging

_HOST_LOGGER_NAMES = ("uvicorn", "celery", "")


class SetupLoggingTests(unittest.TestCase):
    def setUp(self) -> None:
        self._saved: dict[str, tuple[list[logging.Handler], int, bool]] = {}
        names = [*APP_LOGGER_NAMES, *_HOST_LOGGER_NAMES, "httpx", "sqlalchemy.engine"]
        for name in names:
            logger = logging.getLogger(name) if name else logging.getLogger()
            self._saved[name] = (list(logger.handlers), logger.level, logger.propagate)

    def tearDown(self) -> None:
        for name, (handlers, level, propagate) in self._saved.items():
            logger = logging.getLogger(name) if name else logging.getLogger()
            logger.handlers = handlers
            logger.setLevel(level)
            logger.propagate = propagate

    def _clear_hosts(self) -> None:
        logging.getLogger("uvicorn").handlers = []
        logging.getLogger("celery").handlers = []
        logging.getLogger().handlers = []

    def test_reuses_uvicorn_handlers_when_present(self) -> None:
        # Arrange
        self._clear_hosts()
        handler = logging.StreamHandler()
        logging.getLogger("uvicorn").handlers = [handler]
        logging.getLogger("celery").handlers = [logging.StreamHandler()]

        # Act
        setup_logging("DEBUG")

        # Assert
        app_logger = logging.getLogger("agentic_shared")
        self.assertIs(app_logger.handlers[0], handler)
        self.assertEqual(app_logger.level, logging.DEBUG)
        self.assertFalse(app_logger.propagate)
        self.assertIs(logging.getLogger("agentic_api").handlers[0], handler)

    def test_reuses_celery_handlers_without_uvicorn(self) -> None:
        # Arrange
        self._clear_hosts()
        handler = logging.StreamHandler()
        logging.getLogger("celery").handlers = [handler]

        # Act
        setup_logging("INFO")

        # Assert
        app_logger = logging.getLogger("agentic_indexing")
        self.assertIs(app_logger.handlers[0], handler)
        self.assertFalse(app_logger.propagate)

    def test_reuses_root_handlers_when_celery_hijacked_root(self) -> None:
        # Arrange
        self._clear_hosts()
        handler = logging.StreamHandler()
        logging.getLogger().handlers = [handler]

        # Act
        setup_logging("WARNING")

        # Assert
        app_logger = logging.getLogger("agentic_indexing")
        self.assertIs(app_logger.handlers[0], handler)
        self.assertEqual(app_logger.level, logging.WARNING)
        self.assertFalse(app_logger.propagate)

    def test_fallback_handler_without_host(self) -> None:
        # Arrange
        self._clear_hosts()

        # Act
        setup_logging("INFO")

        # Assert
        app_logger = logging.getLogger("agentic_shared")
        self.assertEqual(len(app_logger.handlers), 1)
        self.assertEqual(app_logger.level, logging.INFO)
        self.assertFalse(app_logger.propagate)

    def test_unknown_level_falls_back_to_info(self) -> None:
        # Arrange
        self._clear_hosts()

        # Act
        setup_logging("not-a-level")

        # Assert
        self.assertEqual(logging.getLogger("agentic_shared").level, logging.INFO)

    def test_caps_noisy_third_party_loggers(self) -> None:
        # Arrange
        self._clear_hosts()

        # Act
        setup_logging("DEBUG")

        # Assert
        self.assertEqual(logging.getLogger("httpx").level, logging.WARNING)
        self.assertEqual(logging.getLogger("sqlalchemy.engine").level, logging.WARNING)
        self.assertEqual(logging.getLogger("llama_index").level, logging.WARNING)
        self.assertEqual(logging.getLogger("openai").level, logging.WARNING)


if __name__ == "__main__":
    unittest.main()
