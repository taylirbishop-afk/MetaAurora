# test_metaaurora.py
"""
Tests for MetaAurora module.
"""

import logging
import sys
import unittest
from io import StringIO
from unittest.mock import patch

from metaaurora import MetaAurora, main


class TestMetaAuroraInit(unittest.TestCase):
    """Test cases for MetaAurora initialization."""

    def test_initialization_default(self):
        """Test default (non-verbose) initialization."""
        instance = MetaAurora()
        self.assertIsInstance(instance, MetaAurora)
        self.assertFalse(instance.verbose)

    def test_initialization_verbose(self):
        """Test verbose initialization sets verbose attribute."""
        instance = MetaAurora(verbose=True)
        self.assertIsInstance(instance, MetaAurora)
        self.assertTrue(instance.verbose)

    def test_initialization_returns_logger(self):
        """Test that initialization creates a logger instance."""
        instance = MetaAurora()
        self.assertIsInstance(instance.logger, logging.Logger)


class TestMetaAuroraLogging(unittest.TestCase):
    """Test cases for _setup_logging behavior."""

    def setUp(self):
        # Remove any pre-existing handlers on the module logger between tests
        logger = logging.getLogger("metaaurora")
        logger.handlers.clear()

    def test_default_log_level_is_info(self):
        """Non-verbose mode should set logger level to INFO."""
        instance = MetaAurora(verbose=False)
        self.assertEqual(instance.logger.level, logging.INFO)

    def test_verbose_log_level_is_debug(self):
        """Verbose mode should set logger level to DEBUG."""
        instance = MetaAurora(verbose=True)
        self.assertEqual(instance.logger.level, logging.DEBUG)

    def test_handler_added(self):
        """_setup_logging should add at least one StreamHandler."""
        logger = logging.getLogger("metaaurora")
        logger.handlers.clear()
        instance = MetaAurora()
        stream_handlers = [h for h in instance.logger.handlers
                           if isinstance(h, logging.StreamHandler)]
        self.assertGreater(len(stream_handlers), 0)

    def test_handler_formatter(self):
        """The StreamHandler should use the expected log format."""
        logger = logging.getLogger("metaaurora")
        logger.handlers.clear()
        instance = MetaAurora()
        handler = next(
            h for h in instance.logger.handlers
            if isinstance(h, logging.StreamHandler)
        )
        fmt = handler.formatter._fmt
        self.assertIn("%(asctime)s", fmt)
        self.assertIn("%(name)s", fmt)
        self.assertIn("%(levelname)s", fmt)
        self.assertIn("%(message)s", fmt)


class TestMetaAuroraRun(unittest.TestCase):
    """Test cases for MetaAurora.run()."""

    def test_run_returns_true_on_success(self):
        """run() should return True when no exception is raised."""
        instance = MetaAurora()
        self.assertTrue(instance.run())

    def test_run_returns_false_on_exception(self):
        """run() should return False and log an error when an exception occurs."""
        instance = MetaAurora()
        with patch.object(instance.logger, "info", side_effect=RuntimeError("boom")):
            result = instance.run()
        self.assertFalse(result)

    def test_run_logs_start_message(self):
        """run() should log the start message at INFO level."""
        instance = MetaAurora()
        with patch.object(instance.logger, "info") as mock_info:
            instance.run()
        mock_info.assert_any_call("Starting MetaAurora processing")

    def test_run_logs_completion_message(self):
        """run() should log the completion message at INFO level."""
        instance = MetaAurora()
        with patch.object(instance.logger, "info") as mock_info:
            instance.run()
        mock_info.assert_any_call("Processing completed successfully")

    def test_run_logs_error_on_exception(self):
        """run() should call logger.error when an exception is raised."""
        instance = MetaAurora()
        with patch.object(instance.logger, "info", side_effect=RuntimeError("fail")):
            with patch.object(instance.logger, "error") as mock_error:
                instance.run()
        mock_error.assert_called_once()

    def test_run_verbose_includes_exc_info(self):
        """In verbose mode, run() should pass exc_info=True to logger.error."""
        instance = MetaAurora(verbose=True)
        with patch.object(instance.logger, "info", side_effect=RuntimeError("fail")):
            with patch.object(instance.logger, "error") as mock_error:
                instance.run()
        _, kwargs = mock_error.call_args
        self.assertTrue(kwargs.get("exc_info"))

    def test_run_non_verbose_exc_info_false(self):
        """In non-verbose mode, run() should pass exc_info=False to logger.error."""
        instance = MetaAurora(verbose=False)
        with patch.object(instance.logger, "info", side_effect=RuntimeError("fail")):
            with patch.object(instance.logger, "error") as mock_error:
                instance.run()
        _, kwargs = mock_error.call_args
        self.assertFalse(kwargs.get("exc_info"))


class TestMain(unittest.TestCase):
    """Test cases for the main() CLI entry point."""

    def test_main_exits_successfully(self):
        """main() should not call sys.exit when run succeeds."""
        with patch("sys.argv", ["metaaurora"]):
            try:
                main()
            except SystemExit as exc:
                self.fail(f"main() raised SystemExit({exc.code}) unexpectedly")

    def test_main_exits_with_code_1_on_failure(self):
        """main() should call sys.exit(1) when run() returns False."""
        with patch("sys.argv", ["metaaurora"]):
            with patch.object(MetaAurora, "run", return_value=False):
                with self.assertRaises(SystemExit) as ctx:
                    main()
        self.assertEqual(ctx.exception.code, 1)

    def test_main_verbose_flag(self):
        """main() should pass verbose=True to MetaAurora when -v is given."""
        with patch("sys.argv", ["metaaurora", "--verbose"]):
            with patch("metaaurora.MetaAurora") as MockClass:
                MockClass.return_value.run.return_value = True
                main()
        MockClass.assert_called_once_with(verbose=True)

    def test_main_no_verbose_flag(self):
        """main() should pass verbose=False to MetaAurora by default."""
        with patch("sys.argv", ["metaaurora"]):
            with patch("metaaurora.MetaAurora") as MockClass:
                MockClass.return_value.run.return_value = True
                main()
        MockClass.assert_called_once_with(verbose=False)

    def test_main_short_verbose_flag(self):
        """main() should accept -v as a shorthand for --verbose."""
        with patch("sys.argv", ["metaaurora", "-v"]):
            with patch("metaaurora.MetaAurora") as MockClass:
                MockClass.return_value.run.return_value = True
                main()
        MockClass.assert_called_once_with(verbose=True)


if __name__ == "__main__":
    unittest.main()
