import unittest
from os_tests.libs import utils_lib
from os_tests.libs.file import File


class TestUbuntu(unittest.TestCase):
    def setUp(self):
        utils_lib.init_case(self)

    def test_run_ubuntu_qual(self):
        ubuntu_qual = self.utils_dir + '/ubuntu_qual.sh'
        ubuntu_qual_run = '/tmp/ubuntu_qual.sh'
        if self.params.get('remote_node') is not None:
            self.SSH.put_file(local_file=ubuntu_qual, rmt_file=ubuntu_qual_run)
        else:
            cmd = 'sudo cp -f {} {}'.format(ubuntu_qual,ubuntu_qual_run)
            utils_lib.run_cmd(self, cmd)
        utils_lib.run_cmd(self,"sudo chmod 755 %s" % ubuntu_qual_run)
        utils_lib.run_cmd(self,'sudo bash -c "{}"'.format(ubuntu_qual_run), timeout=500, msg='the system might loss connection if the script cannot finish normally.')
        utils_lib.init_connection(self, timeout=180)
    