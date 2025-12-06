import logging
import os
import tempfile

from selenium.webdriver.firefox.options import Options as FirefoxOptions

logger = logging.getLogger(__name__)


def set_default_firefox_options(
    headless: bool,
    firefox_options: FirefoxOptions,
    browser_profile_output_dir: str | None = None,
) -> FirefoxOptions:
    if browser_profile_output_dir is not None:
        if not os.path.isdir(browser_profile_output_dir):
            raise FileNotFoundError(
                f"Directory does not exist: {browser_profile_output_dir}",
            )
        profile_dir = browser_profile_output_dir
    else:
        profile_dir = tempfile.mkdtemp(prefix="firefox-profile-")

    if headless:
        firefox_options.add_argument("-headless")

    firefox_options.add_argument("-profile")
    firefox_options.add_argument(profile_dir)

    firefox_options.add_argument("--width=1920")
    firefox_options.add_argument("--height=1080")

    firefox_options.set_preference("security.default_personal_cert", "Do not prompt")
    firefox_options.set_preference("security.ask_for_password", 0)
    firefox_options.set_preference("security.enterprise_roots.enabled", False)
    firefox_options.set_preference("security.osclientcerts.autoload", False)
    firefox_options.set_preference("privacy.clearOnShutdown.cookies", True)
    firefox_options.set_preference("privacy.clearOnShutdown.cache", True)
    firefox_options.set_preference("privacy.clearOnShutdown.offlineApps", True)
    firefox_options.set_preference("privacy.clearOnShutdown.history", True)
    firefox_options.set_preference("privacy.clearOnShutdown.formdata", True)
    firefox_options.set_preference("privacy.clearOnShutdown.sessions", True)
    firefox_options.set_preference("privacy.clearOnShutdown.siteSettings", True)
    firefox_options.set_preference("privacy.sanitize.sanitizeOnShutdown", True)
    firefox_options.set_preference("browser.cache.disk.enable", False)
    firefox_options.set_preference("browser.cache.memory.enable", False)
    firefox_options.set_preference("browser.cache.offline.enable", False)
    firefox_options.set_preference("network.http.use-cache", False)

    firefox_options.set_preference("app.update.enabled", False)
    firefox_options.set_preference("app.update.auto", False)
    firefox_options.set_preference("app.update.service.enabled", False)
    firefox_options.set_preference("browser.shell.checkDefaultBrowser", False)
    firefox_options.set_preference("extensions.update.enabled", False)
    firefox_options.set_preference("extensions.update.autoUpdateDefault", False)
    firefox_options.set_preference("extensions.blocklist.enabled", False)
    firefox_options.set_preference("datareporting.healthreport.uploadEnabled", False)
    firefox_options.set_preference("datareporting.policy.dataSubmissionEnabled", False)
    firefox_options.set_preference("browser.tabs.warnOnClose", False)
    firefox_options.set_preference("browser.tabs.warnOnCloseOtherTabs", False)

    firefox_options.set_preference("app.update.staging.enabled", False)
    firefox_options.set_preference("app.update.silent", False)
    firefox_options.set_preference("browser.search.update", False)
    firefox_options.set_preference("toolkit.telemetry.enabled", False)
    firefox_options.set_preference("toolkit.telemetry.unified", False)
    firefox_options.set_preference("toolkit.telemetry.server", "")
    firefox_options.set_preference("toolkit.telemetry.archive.enabled", False)

    firefox_options.set_preference("geo.enabled", True)
    firefox_options.set_preference("permissions.default.geo", 2)
    firefox_options.set_preference("geo.prompt.testing", True)
    firefox_options.set_preference("geo.prompt.testing.allow", False)

    return firefox_options
