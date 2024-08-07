import logging
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from kai.kai_logging import (
    initLogging,
    initLoggingFromConfig,
    process_log_dir_replacements,
    setup_console_handler,
    setup_file_handler,
)
from kai.models.kai_config import KaiConfig, KaiConfigIncidentStore, KaiConfigModels


class TestLoggingSetup(unittest.TestCase):
    def setUp(self):
        self.test_log_dir = tempfile.mkdtemp()
        self.console_log_level = "INFO"
        self.file_log_level = "DEBUG"
        self.log_file = "kai_server.log"
        self.log_dir_with_placeholder = "$pwd/logs"

        # Mock KaiConfig
        self.config = MagicMock(spec=KaiConfig)
        self.config.log_level = self.console_log_level
        self.config.file_log_level = self.file_log_level
        self.config.log_dir = self.log_dir_with_placeholder
        self.config.incident_store = MagicMock(spec=KaiConfigIncidentStore)
        self.config.models = KaiConfigModels(
            provider="FakeProvider",
            args={},
        )
        self.config.solution_consumers = []

    def tearDown(self):
        shutil.rmtree(self.test_log_dir)

    @patch("os.getcwd")
    def test_process_log_dir_replacements(self, mock_getcwd):
        mock_getcwd.return_value = "/home/k8smaster/Desktop/kai/kai"
        print(f"Mocked getcwd: {mock_getcwd.return_value}")
        print(f"Original log_dir: {self.config.log_dir}")

        actual_log_dir = process_log_dir_replacements(self.config.log_dir)

        print(f"Processed log_dir: {actual_log_dir}")
        expected_log_dir = "/home/k8smaster/Desktop/kai/logs"
        print(f"Expected log_dir: {expected_log_dir}")

        self.assertEqual(expected_log_dir, actual_log_dir)

    @patch("logging.StreamHandler")
    def test_setup_console_handler(self, mock_stream_handler):
        logger = logging.getLogger("test_console_logger")
        setup_console_handler(logger, self.console_log_level)
        mock_stream_handler.assert_called_once()
        handler_instance = mock_stream_handler.return_value
        handler_instance.setLevel.assert_called_once_with(self.console_log_level)
        handler_instance.setFormatter.assert_called_once()

    @patch("logging.FileHandler")
    def test_setup_file_handler(self, mock_file_handler):
        logger = logging.getLogger("test_file_logger")
        setup_file_handler(
            logger, self.log_file, self.test_log_dir, self.file_log_level
        )
        mock_file_handler.assert_called_once_with(
            os.path.join(self.test_log_dir, self.log_file)
        )
        handler_instance = mock_file_handler.return_value
        handler_instance.setLevel.assert_called_once_with(self.file_log_level)
        handler_instance.setFormatter.assert_called_once()

    def test_init_logging(self):
        initLogging(
            self.console_log_level,
            self.file_log_level,
            self.test_log_dir,
            self.log_file,
        )
        logger = logging.getLogger("kai")
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertTrue(
            any(
                isinstance(handler, logging.StreamHandler)
                for handler in logger.handlers
            )
        )
        self.assertTrue(
            any(isinstance(handler, logging.FileHandler) for handler in logger.handlers)
        )

    @patch("os.makedirs")
    @patch("os.path.dirname")
    @patch("os.path.realpath")
    def test_init_logging_from_config(self, mock_realpath, mock_dirname, mock_makedirs):
        mock_realpath.return_value = "/home/k8smaster/Desktop/kai/kai"
        mock_dirname.return_value = "/home/k8smaster/Desktop/kai"
        expected_log_dir = "/home/k8smaster/Desktop/kai/logs"

        initLoggingFromConfig(self.config)

        mock_makedirs.assert_called_once_with(expected_log_dir, exist_ok=True)
        logger = logging.getLogger("kai")
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertTrue(
            any(
                isinstance(handler, logging.StreamHandler)
                for handler in logger.handlers
            )
        )
        self.assertTrue(
            any(isinstance(handler, logging.FileHandler) for handler in logger.handlers)
        )


if __name__ == "__main__":
    unittest.main()
