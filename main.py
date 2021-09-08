from tms.bot import TMSBot
from getpass import getpass

from tms.settings import logger, CONFIGPATH, OUTPUTDIR
from tms.utils import yaml_loader, DotDict
import pandas as pd
import os
from datetime import datetime
from pprint import pprint
import time


def make_sure_config_is_available(config):
    try:
        del config["password"]
    except KeyError:
        pass
    pprint(config)


def create_report(data):
    OUTPUTDIR.mkdir(parents=True, exist_ok=True)
    todays_date = str(datetime.now().date())
    file_name = f"{todays_date}.csv"
    if os.path.isfile(OUTPUTDIR / file_name):
        tmp = pd.read_csv(OUTPUTDIR / file_name)
        tmp.append([data])
        tmp.to_csv(f"{OUTPUTDIR}/{file_name}", index=False)
    else:
        pd.DataFrame([data]).to_csv(f"{OUTPUTDIR}/{file_name}", index=False)
    return True


def pipe() -> None:
    last_high_price = 0.0

    logger.info(f"Reading config file from {CONFIGPATH}.")
    config_dict = DotDict(yaml_loader(CONFIGPATH))
    make_sure_config_is_available(yaml_loader(CONFIGPATH))
    to_continue = ""
    while to_continue.lower() not in ["y", "yes", "n", "no"]:
        to_continue = input("You sure you want to continue with these config? [y/n]: ")
    if to_continue.lower() in ["n", "no"]:
        return None

    logger.info("Getting user's credentials.")
    username = config_dict.username
    password = config_dict.password

    while not username:
        username = input("Enter your username: ")
        if username == "q":
            return None

    while not password:
        password = getpass("Enter your password: ")
        if password == "q":
            return None

    if not username and password:
        logger.error(
            "Username and password is requried! \
            Check your credentials.yaml file and follow the instructions."
        )

    logger.info("Launching tmsbot driver.")
    with TMSBot(username=username, password=password) as tmsbot:
        logger.info("Logging in to NEPSE TMS.")
        logged_in = tmsbot.login()
        if not logged_in:
            logger.error("Failed to login to NEPSE TMS.")
            return None
        i = 1
        while True:
            current_time = datetime.now()
            current_time_str = current_time.strftime("%H:%M:%S")
            logger.info(f"Current time is {current_time_str}.")

            _hr, _min = config_dict.time.split(":")
            expected_time = current_time.replace(
                hour=int(_hr), minute=int(_min), second=0
            )
            if expected_time > current_time:
                logger.info(f"Expected to run in  {expected_time}.")
                time_to_run = expected_time - current_time
                logger.info(f"Sleeping for {time_to_run.seconds}")
                time.sleep(time_to_run.seconds)
            logger.info(f"Running iteration {i}")
            buy_status, last_high_price, is_fresh_buy = tmsbot.order_management().buy(
                config=config_dict, last_high_price=last_high_price
            )
            if buy_status:
                tmsbot.refresh()
                if is_fresh_buy:
                    logger.info(f"Creating report of last purchase!")
                    create_report(
                        data={
                            "timestamp": str(current_time),
                            "buy_status": "success",
                            "symbol": config_dict.symbol,
                            "quantity": config_dict.quantity,
                            "price": last_high_price,
                        }
                    )
                i += 1
            else:
                logger.error("Failed to buy. Retrying..")
                continue
        return None


if __name__ == "__main__":
    pipe()
