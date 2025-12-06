import os
from pathlib import Path
import tempfile
import uuid


def helper_function__temp_browser_profile_dir__path(
    create_temp_dir: bool = True,
) -> str:
    temp_browser_profile_dir__path = os.path.join(
        tempfile.gettempdir(),
        f"firefox-profile-{uuid.uuid4()}",
    )
    if create_temp_dir is True:
        Path(temp_browser_profile_dir__path).mkdir(parents=True, exist_ok=True)
    return temp_browser_profile_dir__path
