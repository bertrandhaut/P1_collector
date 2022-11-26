import logging
import logging.config
import os

import yaml
import click
from p1_collector.serial_dsmr import SerialDSMR


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

    measures = SerialDSMR().read_telegram()
    logger.debug(measures)


if __name__ == "__main__":
    cli()