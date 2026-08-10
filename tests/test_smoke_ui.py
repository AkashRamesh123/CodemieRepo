"""UI smoke tests for the docs site under `docs/`:
- Page loads and has the right title
- The Docsify app root is present and visible
- Sanity check: core assets are referenced

Running: `python -m unittest -v`

Environment:
- OPTIONAL `SMOKE_BASE_URL` (e.g. http://localhost:8000/docs/)
- OPTIONAL `SELENIUM_BROWSER` (default: chrome)
- OPTIONAL `HEADLESS` (default: true)

Note: This test module assumes ChromeDriver/GeckoDriver are available on PATH in CI/local runs.
"""

from __future__ import annotations

import os
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def _env_bool(key: str, default: bool) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


class DocsSiteSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        base_url = os.environ.get("SMOKE_BASE_URL", "").strip()
        if not base_url:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            docs_index = os.path.join(repo_root, "docs", "index.html")
            base_url = f"file:///{docs_index}"
        cls.base_url = base_url

    def setUp(self) -> None:
        browser = os.environ.get("SELENIUM_BROWSER", "chrome").strip().lower()
        headless = _env_bool("HEADLESS", True)

        if browser == "firefox":
            opts = webdriver.FirefoxOptions()
            if headless:
                opts.add_argument("-headless")
            self.driver = webdriver.Firefox(options=opts)
        else:
            opts = webdriver.ChromeOptions()
            if headless:
                opts.add_argument("--headless=new")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--window-size=1280,880")
            self.driver = webdriver.Chrome(options=opts)

        self.driver.set_page_load_timeout(30)
        self.wait = WebDriverWait(self.driver, 10)

    def tearDown(self) -> None:
        try:
            self.driver.quit()
        except Exception:
            pass

    def test_docs_homepage_loads_and_has_expected_title(self) -> None:
        self.driver.get(self.base_url)
        self.wait.until(lambda d: d.title.strip() != "")
        self.assertIn("Python Project Collection", self.driver.title)

    def test_docsify_app_container_is_present(self) -> None:
        self.driver.get(self.base_url)
        app = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#app")))
        self.assertTrue(app.is_displayed(), "Docsify root container (#app) should be visible")

    def test_core_assets_are_referenced(self) -> None:
        self.driver.get(self.base_url)
        links = self.driver.find_elements(By.CSS_SELECTOR, "link[rel='stylesheet']")
        hrefs = [l.get_attribute("href") for l in links if l.get_attribute("href")]
        self.assertTrue(any("assets/css/main.css" in h for h in hrefs), "main.css should be referenced")


if __name__ == "__main__":
    unittest.main(verbosity=2)
