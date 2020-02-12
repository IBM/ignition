import os
import string
import unicodedata
import logging
import shutil

logger = logging.getLogger(__name__)

valid_file_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

filename_size_limit = 255


def safe_filename(unsafe_filename):
    # remove spaces
    safe_filename = unsafe_filename.replace(' ', '_')
    # valid ascii
    safe_filename = unicodedata.normalize('NFKD', safe_filename).encode('ASCII', 'ignore').decode()
    # keep valid charts
    safe_filename = ''.join(char for char in safe_filename if char in valid_file_chars)
    if len(safe_filename) > filename_size_limit:
        logger.info("Filename over file name limit {0}, truncating characters. Filename may no longer be unique".format(filename_size_limit))
    return safe_filename[:filename_size_limit]


class DirectoryTree():

    def __init__(self, root_path):
        if root_path is None:
            raise ValueError('root_path argument must be set')
        self.root_path = root_path

    def get_directory_tree(self, directory_path):
        path = os.path.join(self.root_path, directory_path)
        if not os.path.exists(path):
            raise ValueError('No directory at {0} found in root path {1}'.format(directory_path, self.root_path))
        if not os.path.isdir(path):
            raise ValueError('{0} in root path {1} is not a directory'.format(directory_path, self.root_path))
        return DirectoryTree(path)

    def has_directory(self, directory_path):
        path = os.path.join(self.root_path, directory_path)
        if not os.path.exists(path):
            return False
        if not os.path.isdir(path):
            return False
        return True

    def get_file_path(self, file_path):
        path = os.path.join(self.root_path, file_path)
        if not os.path.exists(path):
            raise ValueError('No file at {0} found in root path {1}'.format(file_path, self.root_path))
        if not os.path.isfile(path):
            raise ValueError('{0} in root path {1} is not a file'.format(file_path, self.root_path))
        return path

    def has_file(self, file_path):
        path = os.path.join(self.root_path, file_path)
        if not os.path.exists(path):
            return False
        if not os.path.isfile(path):
            return False
        return True

    def get_path(self):
        return self.root_path

    def remove_all(self, ignore_errors=False):
        if os.path.exists(self.root_path):
            shutil.rmtree(self.root_path, ignore_errors=ignore_errors)

