import unittest
import json
import time
import uuid

from os_tests.libs import utils_lib
from os_tests.libs.volume_manager import VolumeManager
from os_tests.libs.file import File


class TestUbuntu(unittest.TestCase):
    def setUp(self):
        utils_lib.init_case(self)
        self._volume_manager = VolumeManager("ubuntu", self)
        self._volume_id = self._volume_manager.create_volume(100)
        self.file = File(self)
        self._mount_dir = f"/data{str(uuid.uuid4())}"

    def install_fio(self):
        utils_lib.pkg_install(self, "fio", force=True)
        self.assertTrue(utils_lib.is_pkg_installed(self, "fio"))

    def test_ubuntu_fio(self):
        self.install_fio()
        volume_id = str(self._volume_id).replace("-", "")
        time.sleep(15)
        output = utils_lib.run_cmd(
            self,
            "sudo lsblk -o SERIAL,NAME --json",
        )
        self.assertIsNotNone(output)

        data = json.loads(output)
        for device in data["blockdevices"]:
            if device["serial"] == volume_id:
                block_device = f"/dev/{device['name']}"
                utils_lib.run_cmd(
                    self,
                    f"mkfs.xfs -f {block_device} && mkdir {self._mount_dir} && mount -t xfs {block_device} {self._mount_dir}",
                )

        self.assertTrue(self.file.is_directory({self._mount_dir}))
        self.assertTrue(self.file.contains("data", "/proc/mounts"))
        fio_command = f"""fio --name=read_iops_test \
--filename={block_device} \
--filesize=50G \
--time_based \
--ramp_time=2s \
--runtime=1m \
--ioengine=libaio \
--direct=1 \
--verify=0 \
--randrepeat=0 \
--bs=16K \
--iodepth=256 \
--rw=randread"""
        output = utils_lib.run_cmd(self, fio_command, ret_status=True)
        if output != 0:
            self.fail("Fio command failed!")

    def test_

    def tearDown(self):
        utils_lib.run_cmd(self, f"umount {self._mount_dir} && rm -rf {self._mount_dir}")
        self._volume_manager.delete_volume(self._volume_id)
