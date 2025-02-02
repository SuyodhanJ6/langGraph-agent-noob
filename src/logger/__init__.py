# import logging
# import os
# from datetime import datetime

# # Creating logs directory to store log in files
# LOG_DIR = "logs"
# LOG_DIR = os.path.join(os.getcwd(), LOG_DIR)

# # Creating LOG_DIR if it does not exists.
# os.makedirs(LOG_DIR, exist_ok=True)


# # Creating file name for log file based on current timestamp
# CURRENT_TIME_STAMP = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
# file_name = f"log_{CURRENT_TIME_STAMP}.log"

# # Creating file path for projects.
# log_file_path = os.path.join(LOG_DIR, file_name)


# logging.basicConfig(
#     filename=log_file_path,
#     filemode="w",
#     format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
#     level=logging.INFO,
# )
from datetime import datetime
import logging
import os

LOG_FILE_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_FILE_DIR, exist_ok=True)  # Create the directory if it doesn't exist

LOG_FILE_NAME = f"{datetime.now().strftime('%m%d%Y__%H%M%S')}.log"
LOG_FILE_PATH = os.path.join(LOG_FILE_DIR, LOG_FILE_NAME)

logging.basicConfig(
    filename=LOG_FILE_PATH,
    format='[%(asctime)s] \t%(levelname)s \t%(lineno)d \t%(filename)s \t%(funcName)s() \t%(message)s',
    level=logging.INFO,
)
