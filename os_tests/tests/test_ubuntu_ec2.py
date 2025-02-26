import unittest
import json
import time

from os_tests.libs import utils_lib
from os_tests.libs.volume_manager import VolumeManager
from os_tests.libs.file import File


class TestUbuntu(unittest.TestCase):
    def setUp(self):
        utils_lib.init_case(self)
        self._volume_manager = VolumeManager("ubuntu", self)
        self._volume_id = self._volume_manager.create_volume(100)
        self.file = File(self)

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
                    f"mkfs.xfs {block_device} && mkdir /data && mount {block_device} /data",
                )

        self.assertTrue(self.file.is_directory("/data"))
        self.assertTrue(self.file.contains("data", "/proc/mounts"))
        fio_command = """fio --name=read_iops_test \
        --filename=$DEVICE \
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
        output = utils_lib.run_cmd(self, cmd, ret_status=True)
        if output != 0:
            self.fail("Fio command failed!")

    def tearDown(self):
        self._volume_manager.delete_volume(self._volume_id)
        pass
