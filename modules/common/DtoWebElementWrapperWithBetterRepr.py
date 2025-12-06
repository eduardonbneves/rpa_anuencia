from dataclasses import dataclass

from selenium.webdriver.remote.webelement import WebElement


@dataclass
class DtoWebElementWrapperWithBetterRepr:
    webelement: WebElement
    outer_html: str

    def __init__(self, webelement: WebElement):
        self.webelement = webelement
        self.outer_html = webelement.get_attribute("outerHTML")

    def __repr__(self) -> str:
        return (
            f"WebElementWithBetterRepr("
            f"outer_html={self.outer_html!r}, "
            f"webelement={self.webelement!r}"
            f")"
        )
