import subprocess
import logging
import sys

logger = logging.getLogger(__name__)


def run_step(step_name: str, cli_command: list[str]) -> str:
    logger.info(f"Running: {' '.join(cli_command)}")
    try:
        result = subprocess.run(
            args=cli_command, check=True, capture_output=True, text=True
        )
        logger.info(f"'{step_name}' passed.")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"'{step_name}' failed.")
        if e.stdout:
            logger.error(f"stdout:\n{e.stdout}")
        if e.stderr:
            logger.error(f"stderr:\n{e.stderr}")
        sys.exit(e.returncode)
