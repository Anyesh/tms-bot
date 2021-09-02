from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from typing import Tuple

# from tms.handlers import retrieve_company_data, retrieve_people_data
from .utils import DotDict

from .settings import BASEDIR, DRIVERNAME, HEADLESS, TMS_BASE, logger

# from selenium.common.exceptions import TimeoutException

options = Options()
DELAY = 15  # seconds
# options.headless = HEADLESS
if HEADLESS:
    options.add_argument("--headless")


class OrderManagement:
    def __init__(self, order_form: WebDriver):
        self.order_form = order_form

    def buy(self, config: DotDict, last_high_price: float) -> Tuple[bool, float]:
        try:
            logger.info(f"Our last high price is {last_high_price}")
            order_form = self.order_form
            logger.info(f"Filling in symbol name: {config.symbol}")

            symbol_input = order_form.find_element_by_xpath(
                "//input[@typeaheadoptionfield='symbolName']"
            )
            symbol_input.send_keys(config.symbol)
            symbol_info = WebDriverWait(order_form, DELAY).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//typeahead-container[contains(@class, 'dropdown') and contains(@class, 'open')]",
                    )
                )
            )
            full_text = symbol_info.find_element_by_tag_name("span").text
            logger.info(f"Selected {full_text}")
            symbol_input.send_keys(Keys.RETURN)

            # Grab high price
            logger.info("Grabbing high price info")
            high_price_handle: WebDriver = WebDriverWait(order_form, DELAY).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//label[@class='order__form--label' and text()='High']")
                )
            )

            high_price = (
                high_price_handle.find_element_by_xpath("..")
                .find_element_by_tag_name("b")
                .text
            )
            high_price = float(high_price)
            logger.info(f"Current high price is {high_price}")
            if high_price <= last_high_price:
                logger.info("Current is less then last high price so exiting.")
                return (True, high_price)

            logger.info(f"Setting quantity {config.quantity}")
            qty_input = order_form.find_element_by_xpath(
                "//input[@formcontrolname='quantity']"
            )

            qty_input.send_keys(config.quantity)

            logger.info(f"Setting price {high_price}")
            price_input = order_form.find_element_by_xpath(
                "//input[@formcontrolname='price']"
            )
            price_input.send_keys(high_price)

            buy_btn = order_form.find_element_by_xpath(
                "//button[contains(@class, 'btn') and contains(@class, 'btn-sm') and contains(@class, 'btn-primary')]"
            )

            if buy_btn.is_enabled():
                buy_btn.click()
                return (True, high_price)
            else:
                raise Exception("Buy button is disabled")
        except Exception as e:
            logger.error(f"There was an error on buying: {e}")
            return False, 0.0


class TMSBot:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.bot: WebDriver

    def __enter__(self):

        self.bot: WebDriver = webdriver.Firefox(
            options=options,
            executable_path=BASEDIR / "drivers" / DRIVERNAME,
        )

        return self

    def terminate(self):
        self.bot.close()
        self.bot.quit()

    def __exit__(self, type, value, traceback):
        self.terminate()

    def refresh(self):
        self.bot.refresh()

    def order_management(self, delay: int = DELAY) -> OrderManagement:
        _ = WebDriverWait(self.bot, delay).until(
            EC.presence_of_element_located((By.CLASS_NAME, "menu__main"))
        )
        logger.info("Redirecting to order management")
        self.bot.get(TMS_BASE + "/tms/me/memberclientorderentry")

        buy_sell_tab: WebDriver = WebDriverWait(self.bot, DELAY).until(
            EC.presence_of_element_located((By.CLASS_NAME, "xtoggler-control"))
        )
        # toggle_controller = buy_sell_tab.find_element_by_class_name("xtoggler-control")
        toggle_buttons = buy_sell_tab.find_elements_by_xpath(
            "//label[@class='xtoggler-btn-wrapper']"
        )
        logger.info("Setting toggle to BUY")
        toggle_buttons[-1].click()

        order_form = self.bot.find_element_by_xpath(
            "//form[contains(@class, 'order__form ') and contains(@class, 'ng-pristine')]"
        )

        return OrderManagement(order_form)

    def login(self) -> bool:
        is_error = False
        self.bot.get(TMS_BASE + "/login")
        login_page: WebDriver = WebDriverWait(self.bot, DELAY).until(
            EC.presence_of_element_located((By.CLASS_NAME, "login__box"))
        )
        username_field = login_page.find_element_by_xpath("//input[@tabindex='1']")
        password_filed = login_page.find_element_by_id("password-field")
        captcha_field = login_page.find_element_by_id("captchaEnter")

        username_field.clear()
        password_filed.clear()
        captcha_field.clear()
        username_field.send_keys(self.username)
        password_filed.send_keys(self.password)

        # captcha_image = login_page.find_elements_by_class_name(
        #     "captcha-image-dimension"
        # )
        # src = captcha_image[-1].get_attribute("src")  # type: str
        # blob, url = src.split("blob:")
        # urllib.request.urlretrieve(url, "captcha.png")

        captcha = None
        while not captcha:
            captcha = input("Enter your catpcha here: ")
            if captcha == "q":
                return False
        logger.info(f"Given captch is {captcha}")
        captcha_field.send_keys(captcha)

        login_page.find_element_by_xpath(
            "//input[@tabindex='6' and @value='Login']"
        ).click()

        parent_toast = self.bot.find_element_by_id("toasty")
        is_error = parent_toast.find_elements_by_css_selector(
            ".toast.toasty-type-error.toasty-theme-bootstrap"
        )

        return not is_error
