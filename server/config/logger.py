import logging

from logging import FileHandler
from logging import Formatter

LOG_FORMAT = ("%(asctime)s [%(levelname)s]: %(message)s in %(pathname)s:%(lineno)d")
LOG_LEVEL = logging.DEBUG

# sensors logger
SENSORS_LOG_FILE = "./log/sensors.log"

sensors_logger = logging.getLogger("SailUI.sensors")
sensors_logger.setLevel(LOG_LEVEL)
sensors_logger_file_handler = FileHandler(SENSORS_LOG_FILE)
sensors_logger_file_handler.setLevel(LOG_LEVEL)
sensors_logger_file_handler.setFormatter(Formatter(LOG_FORMAT))
sensors_logger.addHandler(sensors_logger_file_handler)

# gnss logger
GNSS_LOG_FILE = "./log/gnss.log"

gnss_logger = logging.getLogger("SailUI.gnss")
gnss_logger.setLevel(LOG_LEVEL)
gnss_file_handler = FileHandler(GNSS_LOG_FILE)
gnss_file_handler.setLevel(LOG_LEVEL)
gnss_file_handler.setFormatter(Formatter(LOG_FORMAT))
gnss_logger.addHandler(gnss_file_handler)

# main logger
MAIN_LOG_FILE = "./log/main.log"

main_logger = logging.getLogger("SailUI.main")
main_logger.setLevel(LOG_LEVEL)
main_logger_file_handler = FileHandler(MAIN_LOG_FILE)
main_logger_file_handler.setLevel(LOG_LEVEL)
main_logger_file_handler.setFormatter(Formatter(LOG_FORMAT))
main_logger.addHandler(main_logger_file_handler)