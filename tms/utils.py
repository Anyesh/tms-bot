import logging
import random
import time

import yaml
from selenium.common.exceptions import NoSuchElementException


def random_nap():
    nap_time = random.randint(30, 300)
    time.sleep(nap_time)


def yaml_loader(yaml_path):
    with open(yaml_path, "r") as d:
        try:
            return yaml.safe_load(d)
        except yaml.YAMLError as exc:
            logging.error(f"There was an error {exc}")
            return None


def check_exists_by_class_name(webdriver, element):
    try:
        webdriver.find_element_by_class_name(element)
    except NoSuchElementException:
        return False
    return True


def check_exists_by_xpath(webdriver, element):
    try:
        webdriver.find_element_by_xpath(element)
    except NoSuchElementException:
        return False
    return True


class DotDict(dict):
    """
    a dictionary that supports dot notation
    as well as dictionary access notation
    usage: d = DotDict() or d = DotDict({'val1':'first'})
    set attributes: d.val2 = 'second' or d['val2'] = 'second'
    get attributes: d.val2 or d['val2']
    """

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__  # type: ignore
    __delattr__ = dict.__delitem__  # type: ignore

    def __init__(self, dct):
        for key, value in dct.items():
            if hasattr(value, "keys"):
                value = DotDict(value)
            self[key] = value
