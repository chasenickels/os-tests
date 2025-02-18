import json
import unittest

from os_tests.libs import utils_lib
from os_tests.libs.file import File


class TestSLES(unittest.TestCase):
    def setUp(self):
        utils_lib.init_case(self)
        self.file = File(self)

    def get_ec2_billing_products(self):
        billing_codes = utils_lib.run_cmd(
            self,
            cmd="ec2metadata --api latest --document"
        )
        data = json.loads(billing_codes)
        return data['billingProducts']

    def is_byos(self):
        service_running = utils_lib.is_service_enabled(self, "guestregister.service")
        pkg_installed = utils_lib.is_pkg_installed(self, "cloud-regionsrv-client", is_install=False)

        if service_running and pkg_installed:
            return False
        else:
            return True

    def is_suma_server(self):
        base_product = utils_lib.run_cmd(self, 'readlink -f "/etc/products.d/baseproduct"').strip("\n")
        suma_server_product = "/etc/products.d/SUSE-Manager-Server.prod"
        suma_server = self.file.exists(suma_server_product)
        return all([
            suma_server,
            base_product == suma_server_product
        ])


    def test_sles_ec2_billing_code(self):
        if utils_lib.is_pkg_installed(self, "python3-ec2metadata", is_install=False):
            products = self.get_ec2_billing_products()
        else:
            self.skipTest("ec2metadata package is not installed.")

        byos = self.is_byos()
        variant = utils_lib.get_os_release_info(self, "VARIANT_ID")

        has_no_code = (
            byos or
            (variant in ('sles-sap', 'sles-sap-hardened') and not byos) or
            self.is_suma_server() and not byos
        )

        if has_no_code:
            self.assertIsNone(products)
        else:
            self.assertIsNotNone(products)

    def test_sles_ec2_dracut_conf(self):
        if utils_lib.determine_architecture(self).upper() != "X86_64":
            self.skipTest(f"Skipping {self._testMethodName}, only x86_64 architecture is tested.")

        needed_drivers = (
            'ena',
            'nvme',
            'nvme-core',
            'virtio',
            'virtio_scsi',
            'xen-blkfront',
            'xen-netfront'
        )
        version = utils_lib.get_os_release_info(self, "VERSION")
        self.assertIsNotNone(version)
        name = utils_lib.get_os_release_info(self, "PRETTY_NAME").lower()
        self.assertIsNotNone(name)

        dracut_file = "/etc/dracut.conf.d/07-aws-type-switch.conf"
        dracut_file_exists = self.file.exists(dracut_file)
        self.assertTrue(dracut_file_exists)

        for driver in needed_drivers:
            if (
                driver.startswith("virtio") and
                (
                    version.startswith("15") or
                    version == "12-SP5" or
                    "micro" in name
                )
            ):
                continue
            self.assertTrue(self.file.contains(driver, dracut_file))


    def test_sles_ec2_network(self):
        pass

    def test_sles_ec2_services(self):
        pass

    def test_sles_ec2_uuid(self):
        pass

    def test_sles_haveged(self):
        pass

    def test_sles_hostname(self):
        pass

    def test_sles_kernel_version(self):
        pass

    def test_sles_license(self):
        pass

    def test_sles_lscpu(self):
        pass

    def test_sles_motd(self):
        pass

    def test_sles_root_pass(self):
        pass