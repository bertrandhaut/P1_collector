import logging
import logging.config
import os

import yaml
import click

from p1_collector.serial_dsmr import SerialDSMR
from p1_collector.sql_output import SQLOutput


logger = logging.getLogger(__name__)


def load_configuration(config_filename=None):
    """
    Load the configuration file
    :param str config_filename: configuration file to load. If None, default config will be loaded
    :return: configuration dict
    :rtype: dict
    """
    config_filename = config_filename or os.path.join(os.path.dirname(__file__), '../data/default_config.yml')

    with open(config_filename, 'r') as f:
        config = yaml.safe_load(f)

    return config


def configure_logger(logging_config):
    logging.config.dictConfig(logging_config)


@click.group()
def cli():
    pass


@cli.command()
@click.option('-c', "--config-file", default=None)
def start(config_file):
    config = load_configuration(config_file)

    configure_logger(config['LOGGING'])
    logger.debug('Logger configured')

    telegram = SerialDSMR().read_telegram()
    logger.debug(f'Telegram at {telegram.timestamp}: \n {telegram}')

    sql_output = SQLOutput(**config['mysql'])
    sql_output.add_measures(telegram)
    logger.debug(f'Telegram sent to DB')


if __name__ == "__main__":
    cli()