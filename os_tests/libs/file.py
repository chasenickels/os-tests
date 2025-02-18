from os_tests.libs import utils_lib


class File:
    def __init__(self, test_instance):
        self.test_instance = test_instance

    def exists(self, file_path):
        if file_path:
            ret = utils_lib.run_cmd(
                self.test_instance,
                cmd="sudo test -e {}".format(file_path),
                ret_status=True,
            )
            if ret == 0:
                return True
        return False

    def is_file(self, file_path):
        if file_path:
            ret = utils_lib.run_cmd(
                self.test_instance,
                cmd="sudo test -f {}".format(file_path),
                ret_status=True,
            )
            if ret == 0:
                return True
        return False

    def is_directory(self, path_name):
        if path_name:
            ret = utils_lib.run_cmd(
                self.test_instance,
                cmd="sudo test -d {}".format(path_name),
                ret_status=True,
            )
            if ret == 0:
                return True
        return False

    def contains(self, pattern, file_path):
        if file_path:
            ret = utils_lib.run_cmd(
                self.test_instance,
                cmd="sudo grep -qs -- {} {}".format(pattern, file_path),
                ret_status=True,
            )
            if ret == 0:
                return True
        return False