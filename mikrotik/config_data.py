import ipaddress
import logging
import os
from configparser import ConfigParser
from typing import Dict, List, Tuple
from gui.utils import get_dir_name


CONFIG_PATH: str = os.path.join(get_dir_name(), "config.ini")
DEFAULT_CONFIG_DATA: Dict[str, str] = {"user": "admin",
                                       "password": "12345"}


def _read_default_user_and_password(config_parser: ConfigParser) -> Dict[str, str]:
    """
    Function reads default username and password for routers.
    :param config_parser: config parser.
    :return: dictionary with default username and password.
    """

    if not config_parser.has_section("MAIN"):
        logging.warning("There are no default user name and password in config file")
        config_parser.add_section("MAIN")
    _default_data = {}
    for subsection in ("user", "password"):
        _default_data[subsection] = config_parser.get("MAIN", subsection,
                                                      fallback=DEFAULT_CONFIG_DATA[subsection])
    return _default_data


def _read_routers_from_config(config_parser: ConfigParser) -> List[Dict[str, str]]:
    """
    Function reads router parameters from config file.
    :param config_parser: config parser.
    :return: list of dictionaries with routers data.
    """

    data = []
    for section in config_parser.sections():
        try:
            ip_address = ipaddress.ip_address(section)
        except Exception:
            continue
        router_data = {"ip_address": ip_address,
                       "user": config_parser.get(section, "user", fallback=None),
                       "password": config_parser.get(section, "password", fallback=None)}
        data.append(router_data)
    return sorted(data, key=lambda x: x["ip_address"])


def _save_default_to_config_file(config_parser: ConfigParser, default_data: Dict[str, str]) -> None:
    """
    Function saves default data (username and password) to config file.
    :param config_parser: config parser;
    :param default_data: dictionary with default username and password.
    """

    config_parser.add_section("MAIN")
    for key, value in default_data.items():
        config_parser.set("MAIN", key, value)


def _save_routers_to_config_file(config_parser: ConfigParser, routers: List[Dict[str, str]]) -> None:
    """
    Function saves data about routers to config file.
    :param config_parser: config parser;
    :param routers: list of dictionaries with routers data.
    """

    for router_data in routers:
        section = str(router_data["ip_address"])
        config_parser.add_section(section)
        if router_data.get("user", None) is not None:
            config_parser.set(section, "user", router_data["user"])
        if router_data.get("password", None) is not None:
            config_parser.set(section, "password", router_data["password"])


def read_config_file() -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """
    Function reads config file.
    :return: dictionary with default username and password and
    list of dictionaries with routers data.
    """

    config_parser = ConfigParser()
    try:
        config_parser.read(CONFIG_PATH)
    except Exception:
        logging.error("Failed to read config file")
    return _read_default_user_and_password(config_parser), _read_routers_from_config(config_parser)


def save_config_file(default_data: Dict[str, str], routers: List[Dict[str, str]]) -> None:
    """
    Function saves config data to config file.
    :param default_data: dictionary with default username and password;
    :param routers: list of dictionaries with routers data.
    """

    config_parser = ConfigParser()
    _save_default_to_config_file(config_parser, default_data)
    _save_routers_to_config_file(config_parser, routers)
    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        config_parser.write(file)
    logging.debug("Routers data saved to config file")
