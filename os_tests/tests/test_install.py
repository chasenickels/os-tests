import json
import unittest

from os_tests.libs import utils_lib


class TestInstall(unittest.TestCase):
    def setUp(self):
        utils_lib.init_case(self)

    def test_install_package(self):
        package = "tree"
        utils_lib.pkg_install(self, package, force=True)

    def test_billing_code(self):
        billing_codes = utils_lib.run_cmd(
            self,
            cmd="ec2metadata --api latest --document"
        )
        data = json.loads(billing_codes)
        return data['billingProducts']

    def tearDown(self):
        utils_lib.finish_case(self)


if __name__ == "__main__":
    unittest.main()
