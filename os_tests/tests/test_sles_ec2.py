import json
import shlex
import unittest

from os_tests.libs import utils_lib
from os_tests.libs.file import File


class TestSLES(unittest.TestCase):
    def setUp(self):
        utils_lib.init_case(self)
        self.file = File(self)

    def get_ec2meta_value(self, value):
        billing_codes = utils_lib.run_cmd(
            self, cmd="ec2metadata --api latest --document"
        )
        data = json.loads(billing_codes)
        return data[value]

    def is_byos(self):
        service_running = utils_lib.is_service_enabled(self, "guestregister.service")
        pkg_installed = utils_lib.is_pkg_installed(
            self, "cloud-regionsrv-client", is_install=False
        )

        if service_running and pkg_installed:
            return False
        else:
            return True

    def is_suma_server(self):
        base_product = utils_lib.run_cmd(
            self, 'readlink -f "/etc/products.d/baseproduct"'
        ).strip("\n")
        suma_server_product = "/etc/products.d/SUSE-Manager-Server.prod"
        suma_server = self.file.exists(suma_server_product)
        return all([suma_server, base_product == suma_server_product])

    def test_sles_ec2_billing_code(self):
        if utils_lib.is_pkg_installed(self, "python3-ec2metadata", is_install=False):
            products = self.get_ec2meta_value("billingProducts")
        else:
            self.skipTest("ec2metadata package is not installed.")

        byos = self.is_byos()
        variant = utils_lib.get_os_release_info(self, "VARIANT_ID")

        has_no_code = (
            byos
            or (variant in ("sles-sap", "sles-sap-hardened") and not byos)
            or self.is_suma_server()
            and not byos
        )

        if has_no_code:
            self.assertIsNone(products)
        else:
            self.assertIsNotNone(products)

    def test_sles_ec2_dracut_conf(self):
        if utils_lib.determine_architecture(self).upper() != "X86_64":
            self.skipTest(
                f"Skipping {self._testMethodName}, only x86_64 architecture is tested."
            )

        needed_drivers = (
            "ena",
            "nvme",
            "nvme-core",
            "virtio",
            "virtio_scsi",
            "xen-blkfront",
            "xen-netfront",
        )
        version = utils_lib.get_os_release_info(self, "VERSION")
        self.assertIsNotNone(version)
        name = utils_lib.get_os_release_info(self, "PRETTY_NAME").lower()
        self.assertIsNotNone(name)

        dracut_file = "/etc/dracut.conf.d/07-aws-type-switch.conf"
        dracut_file_exists = self.file.exists(dracut_file)
        self.assertTrue(dracut_file_exists)

        for driver in needed_drivers:
            if driver.startswith("virtio") and (
                version.startswith("15") or version == "12-SP5" or "micro" in name
            ):
                continue
            self.assertTrue(self.file.contains(driver, dracut_file))

    def test_sles_ec2_network(self):
        current_region = self.get_ec2meta_value("region")
        instance_type = self.get_ec2meta_value("instanceType")

        instance_types = ("c5.large", "i3.8xlarge", "i3.large", "m5.large", "t3.small")
        special_regions = [
            "ap-northeast-3",
            "cn-north-1",
            "cn-northwest-1",
            "us-gov-west-1",
        ]

        if instance_type not in instance_types:
            self.skipTest(f"Unsupported EC2 instance type: {instance_type}.")

        if current_region in special_regions:
            self.skipTest(f"Skipping special region: {current_region}")

        dl_time = 20
        iso_url = f"https://suse-download-test-{current_region}.s3.amazonaws.com/SLE-15-Installer-DVD-x86_64-GM-DVD2.iso"
        curl_cmd = 'curl -o /dev/null --max-time {0} --silent --write-out "%{{size_download}}|%{{http_code}}" {1}'.format(
            dl_time, iso_url
        )
        for i in range(3):
            download_result = utils_lib.run_cmd(self, curl_cmd)

        size, code = download_result.strip().split("|")

        if code == "200" and size == "1214599168":
            return

        if code != "200":
            self.fail(f"Image ISO not found for region: {current_region}")
        elif size != "1214599168":
            self.fail(f"Download failed. Size: {str(size)}")

    def test_sles_ec2_services(self):
        services = ["cloud-init-local", "cloud-init", "cloud-config", "cloud-final"]

        for service in services:
            if not utils_lib.service_result(self, service):
                self.fail(f"Service did not have success result: {service}")

    def test_sles_ec2_uuid(self):
        result = utils_lib.run_cmd(
            self, "sudo cat /sys/devices/virtual/dmi/id/product_uuid"
        ).strip("\n")

        self.assertEqual(result[:3], "ec2")

    def test_sles_haveged(self):
        version = utils_lib.get_os_release_info(self, "VERSION")
        self.assertIsNotNone(version)

        have_haveged = ("12-SP5", "15-SP3")
        if version not in have_haveged:
            self.skipTest("haveged service is only in 12-SP5 and 15-SP3 images")

        pretty_name = utils_lib.get_os_release_info(self, "PRETTY_NAME")

        if "micro" in pretty_name.lower() and float(version) >= 6.0:
            self.skipTest("haveged service is not in micro 6+ images")

        self.assertTrue(
            all(
                [
                    utils_lib.is_service_enabled(self, "haveged"),
                    utils_lib.is_service_running(self, "haveged"),
                ]
            )
        )

    def test_sles_hostname(self):
        result = utils_lib.run_cmd(self, "hostname").strip("\n")

        self.assertNotEqual(result, "linux")

    def test_sles_kernel_version(self):
        version = utils_lib.get_os_release_info(self, "VERSION")
        self.assertIsNotNone(version)
        pretty_name = utils_lib.get_os_release_info(self, "PRETTY_NAME")
        self.assertIsNotNone(pretty_name)

        if version in ("11.4", "12-SP1", "12-SP2", "12-SP3"):
            self.skipTest("Whoops! Image does not have version in kernel config.")

        if "micro" in pretty_name.lower():
            self.skipTest("Micro has product version instead of SLE verison.")

        version = version.split("-SP")
        desired_config_suse_version = f"CONFIG_SUSE_VERSION={version[0]}"
        result = utils_lib.run_cmd(
            self,
            cmd=f"sudo zcat /proc/config.gz | grep -q {desired_config_suse_version}",
            ret_status=True,
        )
        self.assertTrue(result == 0)
        if len(version) > 1:
            desired_config_version_patchlevel = f"CONFIG_SUSE_PATCHLEVEL={version[1]}"
            result = utils_lib.run_cmd(
                self,
                cmd=f"sudo zcat /proc/config.gz | grep -q {desired_config_version_patchlevel}",
                ret_status=True,
            )
            self.assertTrue(result == 0)

    def confirm_license_content(self, license_dirs, license_content):
        for dir in license_dirs:
            if self.file.exists(dir) and self.file.is_directory(dir):
                license = dir + "license.txt"
                return all(
                    [
                        self.file.exists(license),
                        self.file.is_file(license),
                        any(
                            self.file.contains(content, license)
                            for content in license_content
                        ),
                    ]
                )

    def test_sles_license(self):
        license_dirs = [
            "/etc/YaST2/licenses/base/",
            "/etc/YaST2/licenses/SLES/",
            "/usr/share/licenses/product/base/",
            "/usr/share/licenses/product/SLES/",
        ]
        license_content = [
            "SUSE End User License Agreement",
            "SUSE(R) Linux Enterprise End User License Agreement",
            "SUSE® Linux Enterprise End User License Agreement",
            "End User License Agreement for SUSE Products",
        ]

        result = self.confirm_license_content(license_dirs, license_content)
        self.assertTrue(result)

    def test_sles_lscpu(self):
        result = utils_lib.run_cmd(self, "lscpu", ret_status=True)
        if int(result) != 0:
            self.fail("lscpu command failed to run")

    def test_sles_motd(self):
        motd = "/etc/motd"

        if not self.file.exists(motd):
            motd = "/usr/lib/motd.d/10_header"

        self.assertTrue(self.file.exists(motd))
        self.assertTrue(self.file.is_file(motd))

        pretty_name = utils_lib.get_os_release_info(self, "PRETTY_NAME")
        self.assertIsNotNone(pretty_name)

        version = utils_lib.get_os_release_info(self, "VERSION")
        self.assertIsNotNone(pretty_name)

        variant = utils_lib.get_os_release_info(self, "VARIANT_ID") or ""

        if "hardened" in variant.lower():
            self.skipTest("Unable to validate motd in hardened images.")

        self.assertTrue(
            self.file.contains(motd, pretty_name)
            or self.file.contains(
                f"SUSE Linux Enterprise Server {version.replace('-', ' ')}", motd
            )
        )

    def test_sles_root_pass(self):
        result = utils_lib.run_cmd(self, "sudo passwd -S root")
        self.assertTrue(shlex.split(result.strip())[1] in ["L", "LK", "NP"])
