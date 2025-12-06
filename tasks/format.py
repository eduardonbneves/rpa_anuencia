import sys
from tasks.util import run_step

cli_flag_dry_run = "--dry-run" in sys.argv


# [9eee8e5d-e5d7-437e-bac2-cbe99fd678f1] Import sorting is currently handled in the lint step, although it logically belongs in the format step. This inconsistency is acknowledged in the Ruff documentation [1], and a fix is planned for the future.
# [1] https://docs.astral.sh/ruff/formatter/#sorting-imports
STEP_NAME = "LINT and SORT IMPORTS"
STEP_CLI_COMMAND = None
if cli_flag_dry_run is True:
    STEP_CLI_COMMAND = ["ruff", "check"]
else:
    STEP_CLI_COMMAND = ["ruff", "check", "--fix"]
run_step(
    step_name=STEP_NAME,
    cli_command=STEP_CLI_COMMAND,
)

STEP_NAME = "FORMAT"
STEP_CLI_COMMAND = None
if cli_flag_dry_run is True:
    STEP_CLI_COMMAND = ["ruff", "format", "--check"]
else:
    STEP_CLI_COMMAND = ["ruff", "format"]
run_step(
    step_name=STEP_NAME,
    cli_command=STEP_CLI_COMMAND,
)
