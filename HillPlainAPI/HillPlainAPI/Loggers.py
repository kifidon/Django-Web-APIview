import logging
# from .settings import LOG_LEVEL, LOGS_DIR
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError

class AzureBlobHandler(logging.Handler):
    def __init__(self, connection_string, container_name, blob_name):
        super().__init__()
        self.connection_string = connection_string
        self.container_name = container_name
        self.blob_name = blob_name

        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
        self.ensure_container_exists()
        self.upload_blob(self.blob_name, f'Log File: {self.blob_name}')

    def ensure_container_exists(self):
        try:
            self.container_client.create_container()
            print("Container created or already exists.")
        except ResourceExistsError:
            # print("Container already exists.")
            pass
        except Exception as e:
            print(f"Failed to create or access container: {e}")
            raise e

    def upload_blob(self, blob_name, data):
        try:
            self.container_client.get_blob_client(blob_name).upload_blob(data)
            print(f"Blob {blob_name} uploaded successfully.")
        except ResourceNotFoundError as e:
            print(f"Blob {blob_name} not found in the container.")
            raise e
        except Exception as e:
            pass
            # print(f"Error uploading blob: {e}")

    def emit(self, record):
        log_entry = self.format(record)
        try:
            blob_client = self.container_client.get_blob_client(self.blob_name)
            # Append the log entry to the blob
            existing_logs = blob_client.download_blob().readall().decode('utf-8') if blob_client.exists() else ""
            updated_logs = existing_logs + "\n" + log_entry
            blob_client.upload_blob(updated_logs, overwrite=True)
        except Exception as e:
            print(f"Failed to write log to Azure Blob: {e}")


def setup_background_logger(log_level='DEBUG'):
    """
    This function maps the logging data to the /task endpoint logger file.
    """
    logger = logging.getLogger('background_tasks')
    logger.setLevel(log_level)

    # Create a handler for background task logs
    background_handler = logging.FileHandler('BackgroundTasksLog.log')
    background_handler.setLevel(log_level)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    background_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(background_handler)

    return logger


def setup_server_logger(log_level='DEBUG'):
    """
    This function maps the logging data to the / endpoint logger file.
    """
    logger = logging.getLogger('server')
    logger.setLevel(log_level)

    # Create a handler for server logs
    server_handler = logging.FileHandler('ServerLog.log')
    server_handler.setLevel(log_level)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    server_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(server_handler)

    return logger


def setup_sql_logger(log_level='DEBUG'):
    """
    This function maps the logging data to the / endpoint logger file.
    """
    logger = logging.getLogger('sqlLogger')
    logger.setLevel(log_level)

    # Create a handler for SQL logs
    sql_handler = logging.FileHandler('SqlLog.log')
    sql_handler.setLevel(log_level)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    sql_handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(sql_handler)

    return logger