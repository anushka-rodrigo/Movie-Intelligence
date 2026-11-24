import logging

from config.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

logger.info("Logging test started.")
logger.warning("This is a sample warning.")
logger.error("This is a sample error.")

print("\nLogging test completed.")
