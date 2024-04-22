import os
import tempfile

import requests
from requests import Response

from custom_logger.custom_logger import custom_logger

debug, info, error, critical = custom_logger()


def download_atomically(
    fp: str,  # Path where the downloaded file will be stored
    url: str,  # URL from which to download the file
    fmode: str = "wb",  # File mode for opening the temporary file
    chunk_size: int = 8192,  # Chunk size for downloading the file
) -> bool:
    """
    Update a file from the internet in an atomic fashion.

    Parameters:
    - file_path (str): Path where the downloaded file will be stored.
    - url_to_dl (str): URL from which to download the file.
    - fmode (str, optional): File mode for opening the temporary file. Default is "wb".
    - dl_chunk_size (int, optional): Chunk size for downloading the file. Default is 8192 bytes.

    Returns:
    - bool: True if the update is successful, False otherwise.

    Notes:
    - This function downloads a file from the given URL to a temporary file and then atomically replaces the existing file with the downloaded one.
    - Since the file is atomically downloaded, the file is either updated successfully or if the update fails for some reason, the old file is untouched and will be kept as is.
    - If an error occurs during downloading or updating the file, appropriate error messages are logged, and any temporary files are cleaned up.
    """

    # Create a temporary file to download the new content
    temp_file_path = None

    try:
        # Create a temporary file
        temp_file_descriptor, temp_file_path = tempfile.mkstemp()

        # Open the temporary file
        with os.fdopen(fd=temp_file_descriptor, mode=fmode) as temp_file:
            # Make a GET request to download the file content
            response: Response = requests.get(url=url, stream=True, timeout=(10, 10))
            response.raise_for_status()

            # Write the downloaded content to the temporary file in chunks
            for chunk in response.iter_content(chunk_size=chunk_size):
                temp_file.write(chunk)

        # Replace the existing file with the downloaded file atomically
        os.replace(temp_file_path, fp)

        # Log a success message
        info(f"`{fp}` updated successfully!")
        return True

    except (requests.RequestException, OSError) as e:
        error(f"Failed to update file at `{fp}`: {e}")
        return False
    finally:
        # Perform cleanup after update (remove any remaining temporary files)
        if temp_file_path and os.path.exists(temp_file_path):
            info(f"Performing post update cleanup for `{fp}`")
            os.remove(temp_file_path)


def is_internet_accessible() -> bool:
    try:
        response = requests.get("http://google.com", timeout=3)
        if response.status_code // 100 == 2:
            return True
        else:
            return False
    except Exception as err:
        error(f"`is_internet_accessible` function failed: {err}")
        return False
