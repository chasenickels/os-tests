import unittest
from os_tests.libs import utils_lib
from os_tests.libs.resources import UnSupportedAction
import time
import re
import json

class TestCloudInit(unittest.TestCase):
    def setUp(self):
        utils_lib.init_case(self)
        cmd = "sudo systemctl is-enabled cloud-init-local"
        utils_lib.run_cmd(self, cmd, cancel_ret='0', msg = "check cloud-init-local is enabled")
        self.timeout = 180

    def test_check_cloudinit_cfg_no_wheel(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_name:
            test_check_cloudinit_cfg_no_wheel
        component:
            cloud-init
        bugzilla_id:
            1549638
        is_customer_case:
            False
        maintainer:
            xiliang@redhat.com
        description:
            make sure there is no wheel in default_user's group in "/etc/cloud/cloud.cfg"
        key_steps:
            1. check cloud config file
        expect_result:
            there's no 'wheel' saved in log file
        debug_want:
            cloud.cfg
        """
        cmd = 'sudo cat /etc/cloud/cloud.cfg'
        utils_lib.run_cmd(self,
                    cmd,
                    expect_ret=0,
                    expect_not_kw='wheel',
                    msg='check /etc/cloud/cloud.cfg to make sure no wheel in default_user group(bz1549638)')

    def test_check_cloudinit_ds_identify_found(self):
        """
        case_tag:
            cloudinit,cloudinit_tier1
        case_name:
            test_check_cloudinit_ds_identify_found
        component:
            cloud-init
        bugzilla_id:
            1746627
        is_customer_case:
            False
        maintainer:
            xiliang@redhat.com
        description:
            check if ds-identify can run and ret is found
        key_steps:
            1.rpm -q cloud-init
            2.check cloud-init-generator log 
        expect_result:
            no error and return 0
        debug_want:
            cloud init log file
        """
        cmd = 'rpm -q cloud-init'
        utils_lib.run_cmd(self, cmd, cancel_not_kw='el8_0')
        cmd = 'sudo cat /run/cloud-init/cloud-init-generator.log'
        utils_lib.run_cmd(self,
                    cmd,
                    expect_ret=0,
                    expect_kw='ds-identify _RET=found',
                    msg='check /run/cloud-init/cloud-init-generator.log')

    def test_check_cloudinit_fingerprints(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_name:
            test_check_cloudinit_fingerprints
        component:
            cloud-init
        bugzilla_id:
            1957532
        is_customer_case:
            False
        maintainer:
            xiliang@redhat.com
        description:
            check if fingerprints is saved in /var/log/messages.
        key_steps:
            1.sudo awk '/BEGIN/,/END/' /var/log/messages
            2.check result
        expect_result:
            # grep -A 4 'BEGIN SSH HOST KEY FINGERPRINTS' /var/log/messages
            May  6 02:57:58 ip-10-116-2-239 ec2[1441]: -----BEGIN SSH HOST KEY FINGERPRINTS-----
            May  6 02:57:58 ip-10-116-2-239 ec2[1441]: 256 SHA256:n+iS6HUI/ApfkE/ZveBzBrIFSsmcL1YR/c3RsbPShd8 no comment (ECDSA)
            May  6 02:57:58 ip-10-116-2-239 ec2[1441]: 256 SHA256:lZSyEuxf421H9y2DnoadjIvidZWXvGL3wfRlwAFBnms no comment (ED25519)
            May  6 02:57:58 ip-10-116-2-239 ec2[1441]: 3072 SHA256:gysD1LLAkwZIovBEZdzX7s/dCJBegc+jnCtH7cJkIOo no comment (RSA)
            May  6 02:57:58 ip-10-116-2-239 ec2[1441]: -----END SSH HOST KEY FINGERPRINTS-----
        debug_want:
            /var/log/messages
        """
        # cmd = "sudo grep -A 4 'BEGIN SSH HOST KEY FINGERPRINTS' /var/log/messages"
        cmd = "sudo awk '/BEGIN/,/END/' /var/log/messages"
        out = utils_lib.run_cmd(self, cmd, msg='get fingerprints in /var/log/messages')
        if out.count('BEGIN') != out.count('SHA256')/3:
            self.fail('fingerprints count {} does not match expected {}'.format(out.count('SHA256')/3,out.count('BEGIN')))

    def test_check_cloudinit_log_imdsv2(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_name:
            test_check_cloudinit_log_imdsv2
        case_file:
            test_cloud_init.py
        component:
            kernel
        bugzilla_id:
            1810704
        is_customer_case:
            True
        testplan:
            N/A
        maintainer:
            xiliang@redhat.com
        description:
            Check cloud-init use imdsv2 in aws
        key_steps:
            1.#sudo grep -Ri amazon /sys/devices/virtual/dmi/id/bios*
            2.#sudo rpm -ql cloud-init|grep -w DataSourceEc2.py
            3.#sudo cat "output of step2"|grep IMDSv2
            4.#sudo cat /var/log/cloud-init.log
        expect_result:
            There is keyword "Fetching Ec2 IMDSv2 API Token,X-aws-ec2-metadata-token' in /var/log/cloud-init.log.
        debug_want:
            cloud-init
        """
        cmd = "sudo grep -Ri amazon /sys/devices/virtual/dmi/id/bios*"
        utils_lib.run_cmd(self, cmd, cancel_ret='0', msg = "Only used in EC2 platform")
        cmd = "sudo rpm -ql cloud-init|grep -w DataSourceEc2.py"
        output = utils_lib.run_cmd(self, cmd, expect_ret=0, msg='Get DataSourceEc2.py')
        cmd = "sudo cat " + output + "|grep IMDSv2"
        utils_lib.run_cmd(self, cmd,
                    cancel_kw="Fetching Ec2 IMDSv2 API Token",
                    msg='Check IMDSv2 support')
        utils_lib.run_cmd(self,
                    'sudo cat /var/log/cloud-init.log',
                    expect_ret=0,
                    expect_kw='Fetching Ec2 IMDSv2 API Token,X-aws-ec2-metadata-token',
                    msg='check /var/log/cloud-init.log')

    def test_check_cloudinit_log_unexpected(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_name:
            test_check_cloudinit_log_unexpected
        component:
            cloud-init
        bugzilla_id:
            1827207
        is_customer_case:
            False
        maintainer:
            xiliang@redhat.com
        description:
            check no unexpected error log in cloudinit logs
        key_steps:
            1.check there is no unexpected saved in cloud init log
        expect_result:
            no token saved in log
        debug_want:
            cloud init log
        """
        utils_lib.run_cmd(self,
                    'sudo cat /var/log/cloud-init.log',
                    expect_ret=0,
                    expect_not_kw='unexpected',
                    msg='check /var/log/cloud-init.log')
        if 'release 7' not in utils_lib.run_cmd(self,
                                          'sudo cat /etc/redhat-release'):
            utils_lib.run_cmd(self,
                        'sudo cat /var/log/cloud-init-output.log',
                        expect_ret=0,
                        expect_not_kw='unexpected',
                        msg='check /var/log/cloud-init-output.log')

    def test_check_cloudinit_log_critical(self):
        """
        case_tag:
            cloudinit,cloudinit_tier1
        case_name:
            test_check_cloudinit_log_critical
        component:
            cloud-init
        bugzilla_id:
            1827207
        is_customer_case:
            False
        maintainer:
            xiliang@redhat.com
        description:
            check if there is CRITICAL saved in log file
        key_steps:
            1. check cloud init log file
        expect_result:
            no CRITICAL saved in log file
        debug_want:
            cloud init log file
        """
        utils_lib.run_cmd(self,
                    'sudo cat /var/log/cloud-init.log',
                    expect_ret=0,
                    expect_not_kw='CRITICAL',
                    msg='check /var/log/cloud-init.log')
        if 'release 7' not in utils_lib.run_cmd(self,
                                          'sudo cat /etc/redhat-release'):
            utils_lib.run_cmd(self,
                        'sudo cat /var/log/cloud-init-output.log',
                        expect_ret=0,
                        expect_not_kw='CRITICAL',
                        msg='check /var/log/cloud-init-output.log')

    def test_check_cloudinit_log_warn(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_name:
            test_check_cloudinit_log_warn
        component:
            cloud-init
        bugzilla_id:
            1821999
        is_customer_case:
            False
        maintainer:
            xiliang@redhat.com
        description:
            check no warning log in cloudinit logs
        key_steps:
            1.check if there are WARNING in cloud-init.log
        expect_result:
            no WARNING saved in log file
        debug_want:
            cloud init log file
        """
        utils_lib.run_cmd(self,
                    'sudo cat /var/log/cloud-init.log',
                    expect_ret=0,
                    expect_not_kw='WARNING',
                    msg='check /var/log/cloud-init.log')
        if 'release 7' not in utils_lib.run_cmd(self,
                                          'sudo cat /etc/redhat-release'):
            utils_lib.run_cmd(self,
                        'sudo cat /var/log/cloud-init-output.log',
                        expect_ret=0,
                        expect_not_kw='WARNING',
                        msg='check /var/log/cloud-init-output.log')

    def test_check_cloudinit_log_error(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_name:
            test_check_cloudinit_log_error
        component:
            cloud-init
        bugzilla_id:
            1821999
        is_customer_case:
            False
        maintainer:
            xiliang@redhat.com
        description:
            check if there is error log in cloud init log file
        key_steps:
            1.check cloud init log file
        expect_result:
            there is no ERROR saved in log file
        debug_want:
            cloud init log file
        """
        utils_lib.run_cmd(self,
                    'sudo cat /var/log/cloud-init.log',
                    expect_ret=0,
                    expect_not_kw='ERROR',
                    msg='check /var/log/cloud-init.log')
        if 'release 7' not in utils_lib.run_cmd(self,
                                          'sudo cat /etc/redhat-release'):
            utils_lib.run_cmd(self,
                        'sudo cat /var/log/cloud-init-output.log',
                        expect_ret=0,
                        expect_not_kw='ERROR',
                        msg='check /var/log/cloud-init-output.log')

    def test_check_cloudinit_log_traceback(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_name:
            test_check_cloudinit_log_traceback
        component:
            cloud-init
        bugzilla_id:
            N/A
        is_customer_case:
            False
        maintainer:
            xiliang@redhat.com
        description:
            check if there's no traceback log in cloudinit logs
        key_steps:
            1.check cloud-init log file
        expect_result:
            no Traceback saved in log file
        debug_want:
            cloud-init log file
        """
        utils_lib.run_cmd(self,
                    'sudo cat /var/log/cloud-init.log',
                    expect_ret=0,
                    expect_not_kw='Traceback',
                    msg='check /var/log/cloud-init.log')
        if 'release 7' not in utils_lib.run_cmd(self,
                                          'sudo cat /etc/redhat-release'):
            utils_lib.run_cmd(self,
                        'sudo cat /var/log/cloud-init-output.log',
                        expect_ret=0,
                        expect_not_kw='Traceback',
                        msg='check /var/log/cloud-init-output.log')

    def test_check_metadata(self):
        '''
        case_tag:
            cloudinit,cloudinit_tier2
        polarion_id:
        description:
            https://cloudinit.readthedocs.io/en/latest/topics/datasources/ec2.html
        '''
        if self.vm.provider == 'nutanix':
            self.skipTest('skip run for nutanix platform on which use config drive to fetch metadata but not http service')
        cmd = r"curl http://169.254.169.254/latest/meta-data/instance-type"

        utils_lib.run_cmd(self, cmd, expect_ret=0, expect_not_kw="Not Found")

    def test_check_output_isexist(self):
        '''
        case_tag:
            cloudinit,cloudinit_tier1
        polarion_id:
        bz: 1626117
        description:
            check whether /var/log/cloud-init-output.log exists
        '''
        utils_lib.run_cmd(self,
                    'uname -r',
                    cancel_not_kw='el7,el6',
                    msg='cancel it in RHEL7')
        datasource = None
        if utils_lib.is_ali(self):
            datasource = 'Datasource DataSourceAliYun'
        if utils_lib.is_aws(self):
            datasource = 'Datasource DataSourceEc2'
        cmd = 'sudo cat /var/log/cloud-init-output.log'
        if datasource is not None:    
            utils_lib.run_cmd(self,
                        cmd,
                        expect_kw=datasource,
                        msg='check /var/log/cloud-init-output.log exists status')
        else:
            utils_lib.run_cmd(self,
                        cmd,
                        expect_ret=0,
                        msg='check /var/log/cloud-init-output.log exists status')

    def test_check_cloudinit_service_status(self):
        """
        case_tag:
            cloudinit,cloudinit_tier1
        case_name:
            test_check_cloudinit_service_status
        component:
            cloud-init
        bugzilla_id:
            1829713
        is_customer_case:
            False
        maintainer:
            xiliang@redhat.com
        description:
            The 4 cloud-init services status should be "active"
        key_steps:
            1.start a RHEL-7.9 AMI on aws and check service status
        expect_result:
            cloud-final.service not failed
        debug_want:
            N/A
        """
        service_list = ['cloud-init-local',
                        'cloud-init',
                        'cloud-config',
                        'cloud-final']
        for service in service_list:
            cmd = "sudo systemctl status %s" % service
            utils_lib.run_cmd(self, cmd, expect_ret=0, expect_kw='Active: active', msg = "check %s status" % service)
            cmd = "sudo systemctl is-active %s" % service
            utils_lib.run_cmd(self, cmd, expect_ret=0, expect_kw='active', msg = "check %s status" % service)

    def test_cloudinit_sshd_keypair(self):
        '''
        case_tag:
            cloudinit,cloudinit_tier2
        case_file:
            https://github.com/liangxiao1/os-tests/blob/master/os_tests/tests/test_cloud_init.py
        description:
            The '/etc/ssh/sshd_config' allows key value empty, this case check if cloud-init can handle such situation.
        testplan:
            n/a
        bugzilla_id: 
            1527649, 1862933
        is_customer_case: 
            True
        maintainer: 
            xiliang
        case_priority: 
            2
        component: 
            cloud-init
        key_steps: |
            # sudo echo 'DenyUsers'>>/etc/ssh/sshd_config
            # sudo cloud-init clean
            # sudo grep 'SSH credentials failed' /var/log/cloud-init.log
        expect_result: 
            No 'SSH credentials failed' found
        debug_want:
            Please attach /var/log/cloud-init.log
        '''
        cmd = 'cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys.bak'
        utils_lib.run_cmd(self, cmd, msg='backup .ssh/authorized_keys')
        cmd = 'sudo cp -f /etc/ssh/sshd_config /etc/ssh/sshd_config.bak'
        utils_lib.run_cmd(self, cmd, msg='backup /etc/ssh/sshd_config')
        cmd = "sudo sed -i '/DenyUsers/d' /etc/ssh/sshd_config"
        utils_lib.run_cmd(self, cmd, msg='delete old config if has')
        cmd = "sudo bash -c 'echo DenyUsers >> /etc/ssh/sshd_config'"
        utils_lib.run_cmd(self, cmd, msg='append empty DenyUsers filed')
        cmd = "sudo cloud-init clean"
        utils_lib.run_cmd(self, cmd, msg='clean cloud-init')
        cmd = "sudo cloud-init init"
        utils_lib.run_cmd(self, cmd, msg='init cloud-init again')
        cmd = 'sudo cp -f /etc/ssh/sshd_config.bak /etc/ssh/sshd_config'
        utils_lib.run_cmd(self, cmd, msg='restore /etc/ssh/sshd_config')  
        utils_lib.run_cmd(self,
                    'sudo cat /var/log/cloud-init.log',
                    expect_ret=0,
                    expect_not_kw='SSH credentials failed',
                    expect_kw='value pair',
                    msg='check /var/log/cloud-init.log')  

    def _get_boot_temp_devices(self):
        out = utils_lib.run_cmd(self,"lsblk -d|awk -F' ' '{print $1}'", msg='get all disks')
        disks = out.split('\n')
        boot_dev = '/dev/sda'
        boot_part = utils_lib.run_cmd(self,'mount|grep boot|head -1', msg='get boot part')
        for disk in disks:
            if disk in boot_part:
                boot_dev = disk
                break
        self.log.info("Detected boot device:{}".format(boot_dev))
        return boot_dev

    def test_cloudinit_auto_extend_root_partition_and_filesystem(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_name:
            test_cloudinit_auto_extend_root_partition_and_filesystem
        case_file:
            os_tests.tests.test_cloud_init.TestCloudInit.test_cloudinit_auto_extend_root_partition_and_filesystem
        component:
            cloud-init,cloud_utils_growpart
        bugzilla_id:
            1447177
        is_customer_case:
            N/A
        testplan:
            N/A
        maintainer:
            minl@redha.tcom
        description:
            RHEL7-103839 - CLOUDINIT-TC: Auto extend root partition and filesystem
        key_steps: |
            1. Install cloud-utils-growpart gdisk if not installed(bug 1447177)
            2. Check os disk and fs capacity
            3. Enlarge os disk
            4. Check os disk and fs capacity
        expect_result:
            1. OS disk and fs capacity check right.
        debug_want:
            N/A
        """
        if not self.vm:
            self.skipTest("Skip this test case as no vm inited")

        # 1. Install cloud-utils-growpart gdisk
        utils_lib.is_cmd_exist(self, cmd='growpart')
        utils_lib.is_cmd_exist(self, cmd='gdisk')
        
        # 2. Check os disk and fs capacity
        boot_dev = self._get_boot_temp_devices()
        dev_size = utils_lib.run_cmd(self, "lsblk /dev/{0} --output NAME,SIZE -r |grep -o -P '(?<={0} ).*(?=G)'".format(boot_dev))
        os_disk_size = int(self.vm.show()['vm_disk_info'][0]['size'])/(1024*1024*1024)
        self.assertAlmostEqual(
            first=float(dev_size),
            second=float(os_disk_size),
            delta=1,
            msg="Device size is incorrect. Raw disk: %s, real: %s" %(dev_size, os_disk_size)
        )
        # 3. Enlarge os disk size
        try:
            self.disk.modify_disk_size(os_disk_size, 'scsi', 0, 2)
        except NotImplementedError:
            self.skipTest('modify disk size func is not implemented in {}'.format(self.vm.provider))
        except UnSupportedAction:
            self.skipTest('modify disk size func is not supported in {}'.format(self.vm.provider))
        utils_lib.run_cmd(self, 'sudo reboot', msg='reboot system under test')
        time.sleep(10)
        utils_lib.init_connection(self, timeout=1200)
        boot_dev = self._get_boot_temp_devices()
        partition = utils_lib.run_cmd(self,
            "find /dev/ -name {}[0-9]|sort|tail -n 1".format(boot_dev)).replace('\n', '')
        new_dev_size = utils_lib.run_cmd(self,
            "lsblk /dev/{0} --output NAME,SIZE -r"
            "|grep -o -P '(?<={0} ).*(?=G)'".format(boot_dev))
        new_fs_size = utils_lib.run_cmd(self,
            "df {} --output=size -h|grep -o '[0-9]\+'".format(partition))
        new_os_disk_size=os_disk_size+2
        self.assertEqual(
            int(new_dev_size), int(new_os_disk_size),
            "New device size is incorrect. "
            "Device: %s, real: %s" % (new_dev_size, new_os_disk_size)
        )
        self.assertAlmostEqual(
            first=float(new_fs_size),
            second=float(new_os_disk_size),
            delta=1.5,
            msg="New filesystem size is incorrect. "
                "FS: %s, real: %s" %
                (new_fs_size, new_os_disk_size)
        )

    def test_cloudinit_login_with_password(self):
        """
        case_tag:
            cloudinit,cloudinit_tier1
        case_name:
            test_cloudinit_login_with_password
        case_file:
            os_tests.tests.test_cloud_init.TestCloudInit.test_cloudinit_login_with_password
        component:
            cloudinit
        bugzilla_id:
            N/A
        is_customer_case:
            False
        testplan:
            N/A
        maintainer:
            minl@redhat.com
        description:
            VM can successfully login after provisioning(with password authentication)
        key_steps:
            1. Create a VM with only password authentication
        expect_result:
            1. Login with password, should have sudo privilege
        debug_want:
            N/A
        """
        if not self.vm:
            self.skipTest("Skip this test case as no vm inited")
        if self.vm.provider == 'openstack':
            self.skipTest('skip run as openstack uses userdata to config the password')
        for attrname in ['ssh_pubkey', 'get_vm_by_filter', 'prism']:
            if not hasattr(self.vm, attrname):
                self.skipTest("no {} for {} vm".format(attrname, self.vm.provider))
        if self.vm.exists():
            self.vm.delete()
            time.sleep(30)
        save_ssh_pubkey = self.vm.ssh_pubkey
        self.vm.ssh_pubkey = None
        self.vm.create(wait=True)
        #test passwork login to new vm
        NewVM = self.vm.get_vm_by_filter("vm_name", self.vm.vm_name)
        start_task = self.vm.prism.start_vm(NewVM['uuid'])
        self.log.info("start task status is %s" % format(start_task))
        time.sleep(60)
        for nic in NewVM.get('vm_nics'):
            if nic['network_uuid'] == self.vm.network_uuid:
                NewVM_ip = nic['ip_address']
        test_login = utils_lib.send_ssh_cmd(NewVM_ip, self.vm.vm_username, self.vm.vm_password, "whoami")
        self.assertEqual(self.vm.vm_username,
                         test_login[1].strip(),
                         "Fail to login with password: %s" % format(test_login[1].strip()))
        test_sudo = utils_lib.send_ssh_cmd(NewVM_ip, self.vm.vm_username, self.vm.vm_password, "sudo cat /etc/sudoers.d/90-cloud-init-users")
        self.assertIn(self.vm.vm_username,
                         test_sudo[1].strip(),
                         "Fail to check login user name: %s" % format(test_sudo[1].strip()))
        #teardown
        self.vm.ssh_pubkey=save_ssh_pubkey
        self.vm.delete()
        self.vm.create(wait=True)
        self.vm.start(wait=True)
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)

    def test_cloudinit_verify_hostname(self):
        """
        case_tag:
            cloudinit,cloudinit_tier1
        case_name:
            test_cloudinit_verify_hostname
        case_file:
            os_tests.tests.test_cloud_init.TestCloudInit.test_cloudinit_verify_hostname
        component:
            cloudinit
        bugzilla_id:
            N/A
        is_customer_case:
            False
        testplan:
            N/A
        maintainer:
            minl@redhat.com
        description:
            Successfully set VM hostname
        key_steps:
            1. Check hostname by different command
        expect_result:
            1. Host name is correct
        debug_want:
            N/A
        """
        for cmd in ['hostname', 'nmcli general hostname', 'hostnamectl|grep Static']:
            check_hostname = utils_lib.run_cmd(self, 'sudo cat /var/log/cloud-init.log', expect_ret=0)
            self.assertIn(self.vm.vm_name, check_hostname, "'%s': Hostname is not correct" % cmd)

    def _cloudinit_auto_resize_partition(self, label):
        """
        :param label: msdos/gpt
        """
        utils_lib.run_cmd(self, "sudo su -")
        utils_lib.run_cmd(self, "which growpart", expect_ret=0, msg="test growpart command.")
        device = "/tmp/testdisk"
        if "/dev" not in device:
            utils_lib.run_cmd(self, "rm -f {}".format(device))
        utils_lib.run_cmd(self, "truncate -s 2G {}".format(device))
        utils_lib.run_cmd(self, "parted -s {} mklabel {}".format(device, label))
        part_type = "primary" if label == "msdos" else ""
         # 1 partition
        utils_lib.run_cmd(self, "parted -s {} mkpart {} xfs 0 1000".format(device, part_type))
        utils_lib.run_cmd(self, "parted -s {} print".format(device))
        utils_lib.run_cmd(self, "growpart {} 1".format(device), expect_ret=0, msg="test to run growpart")
        self.assertEqual(
            "2147MB",
            utils_lib.run_cmd(self,
                "parted -s %s print|grep ' 1 '|awk '{print $3}'" % device, expect_ret=0).strip(),
            "Fail to resize partition")
        # 2 partitions
        utils_lib.run_cmd(self, "parted -s {} rm 1".format(device))
        utils_lib.run_cmd(self,
            "parted -s {} mkpart {} xfs 0 1000".format(device, part_type))
        utils_lib.run_cmd(self,
            "parted -s {} mkpart {} xfs 1800 1900".format(device, part_type))
        utils_lib.run_cmd(self, "parted -s {} print".format(device))
        utils_lib.run_cmd(self, "growpart {} 1".format(device), expect_ret=0)
        self.assertEqual(
            "1800MB",
            utils_lib.run_cmd(self,
                "parted -s %s print|grep ' 1 '|awk '{print $3}'" % device, expect_ret=0).strip(),
            "Fail to resize partition")

    def test_cloudinit_auto_resize_partition_in_gpt(self):
        """
        case_tag:
            cloud_utils_growpart,cloud_utils_growpart_tier1
        case_name:
            test_cloudinit_auto_resize_partition_in_gpt
        case_file:
            os_tests.tests.test_cloud_init.TestCloudInit.test_cloudinit_auto_resize_partition_in_gpt
        component:
            cloudinit
        bugzilla_id:
            1695091
        is_customer_case:
            False
        testplan:
            N/A
        maintainer:
            minl@redhat.com
        description:
            Auto resize partition in gpt
        key_steps:
            1. parted and growpart command
        expect_result:
            1. Successfully resize partition in gpt
        debug_want:
            N/A
        """
        self._cloudinit_auto_resize_partition("gpt")

    def test_cloudinit_auto_resize_partition_in_mbr(self):
        """
        case_tag:
            cloud_utils_growpart,cloud_utils_growpart_tier1
        case_name:
            test_cloudinit_auto_resize_partition_in_mbr
        case_file:
            os_tests.tests.test_cloud_init.TestCloudInit.test_cloudinit_auto_resize_partition_in_mbr
        component:
            cloudinit
        bugzilla_id:
            N/A
        is_customer_case:
            False
        testplan:
            N/A
        maintainer:
            minl@redhat.com
        description:
            Auto resize partition in mbr
        key_steps:
            1. parted and growpart command
        expect_result:
            1. Successfully resize partition in mbr
        debug_want:
            N/A
        """
        self._cloudinit_auto_resize_partition("msdos")

    def test_cloudinit_start_sector_equal_to_partition_size(self):
        """
        case_tag:
            cloud_utils_growpart,cloud_utils_growpart_tier1
        case_name:
            test_cloudinit_start_sector_equal_to_partition_size
        case_file:
            os_tests.tests.test_cloud_init.TestCloudInit.test_cloudinit_start_sector_equal_to_partition_size
        component:
            cloudinit
        bugzilla_id:
            1593451
        is_customer_case:
            False
        testplan:
            N/A
        maintainer:
            minl@redhat.com
        description:
            Start sector equal to partition size
        key_steps:
            1. Check start sector
        expect_result:
            1. Start sector equal to partition size
        debug_want:
            N/A
        """
        utils_lib.run_cmd(self, "sudo su -")
        utils_lib.run_cmd(self, "which growpart", expect_ret=0, msg="test growpart command.")
        device = "/tmp/testdisk"
        if "/dev" not in device:
            utils_lib.run_cmd(self, "rm -f {}".format(device), expect_ret=0)
        utils_lib.run_cmd(self, "truncate -s 2G {}".format(device), expect_ret=0)
        size = "1026048"
        utils_lib.run_cmd(self, """
cat > partitions.txt <<EOF
# partition table of {0}
unit: sectors

{0}1 : start= 2048, size= 1024000, Id=83
{0}2 : start= {1}, size= {1}, Id=83
EOF""".format(device, size), expect_ret=0)
        utils_lib.run_cmd(self, "sfdisk {} < partitions.txt".format(device), expect_ret=0)
        utils_lib.run_cmd(self, "growpart {} 2".format(device), expect_ret=0)
        start = utils_lib.run_cmd(self,
            "parted -s %s unit s print|grep ' 2 '|awk '{print $2}'" % device, expect_ret=0)
        end = utils_lib.run_cmd(self,
            "parted -s %s unit s print|grep ' 2 '|awk '{print $3}'" % device, expect_ret=0)
        self.assertEqual(start.strip(), size + 's', "Start size is not correct")
        self.assertEqual(end.strip(), '4194270s', "End size is not correct")

    def test_cloudinit_save_and_handle_customdata_script(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_name:
            test_cloudinit_save_and_handle_customdata_script
        case_file:
            os_tests.tests.test_cloud_init.TestCloudInit.test_cloudinit_save_and_handle_customdata_script
        component:
            cloudinit
        bugzilla_id:
            N/A
        is_customer_case:
            False
        testplan:
            N/A
        maintainer:
            minl@redhat.com
        description:
            Test if custom data as script can be executed. File test.sh has be pre-uploaded and configured when provision VM.
        key_steps: |
            1. Create VM with custom data.
            2. Check if custom data as script can be executed.
        expect_result:
            Custom data as script can be executed.
        debug_want:
            N/A
        """
        if self.vm.provider != 'nutanix':
            self.skipTest('skip run as this needs to configure vm_custom_file, configured on nutanix')
        utils_lib.run_cmd(self,"sudo chmod 777 /tmp/%s" % self.vm.prism.vm_custom_file)
        utils_lib.run_cmd(self,"sudo /tmp/%s" % self.vm.prism.vm_custom_file)
        self.assertEqual("Test files to copy",
                         utils_lib.run_cmd(self, "sudo cat /tmp/test.txt").strip(),
                         "The custom data script is not executed correctly.")

    def test_cloudinit_save_and_handle_customdata_cloudinit_config(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_name:
            test_cloudinit_save_and_handle_customdata_cloudinit_config
        case_file:
            os_tests.tests.test_cloud_init.TestCloudInit.test_cloudinit_save_and_handle_customdata_cloudinit_config
        component:
            cloudinit
        bugzilla_id:
            N/A
        is_customer_case:
            False
        testplan:
            N/A
        maintainer:
            minl@redhat.com
        description:
            Test if the new cloud-init configuration is handled correctly
        key_steps: |
            1. Create VM with custom data.
            2. Check if the new cloud-init configuration is handled correctly.
        expect_result:
            The new cloud-init configuration is handled correctly.
        debug_want:
            N/A
        """
        if self.vm.provider != 'nutanix':
            self.skipTest('skip run as this needs to configure userdata, configured on nutanix')
        output = utils_lib.run_cmd(self,
            "sudo grep 'running modules for config' "
            "/var/log/cloud-init.log -B 10")
        self.assertIn("Ran 6 modules", output,
                      "The custom data is not handled correctly")

    def test_cloudinit_provision_vm_with_multiple_nics(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_name:
            test_cloudinit_provision_vm_with_multiple_nics
        case_file:
            os_tests.tests.test_cloud_init.TestCloudInit.test_cloudinit_provision_vm_with_multiple_nics
        component:
            cloudinit
        bugzilla_id:
            N/A
        is_customer_case:
            False
        testplan:
            N/A
        maintainer:
            minl@redhat.com
        description:
            Provision VM with multiple NICs
        key_steps: |
            1. Create a VM with 2 NICs.
            2. Check if can provision and connect to the VM successfully.
        expect_result:
            VM can provision and connect successfully
        debug_want:
            N/A
        """
        if not self.vm:
            self.skipTest("Skip this test case as no vm inited")
        if self.vm.provider != 'nutanix':
            self.skipTest('skip run as this needs to configure single_nic, configured on nutanix')
        self.vm.delete(wait=True)
        self.vm.create(single_nic=False, wait=True)
        self.vm.start(wait=True)
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)
        ip_list_vm = utils_lib.run_cmd(self,
            "ip addr|grep -Po 'inet \\K.*(?=/)'|grep -v '127.0.0.1'").strip().split('\n')
        ip_list_vm.sort()
        ip_list_host = []
        for nic in self.vm.show()["vm_nics"]:
            ip_list_host.append(nic["ip_address"])
        ip_list_host.sort()
        self.assertGreater(len(ip_list_vm), 1, "VM not create by multi nics")
        self.assertEqual(
            ip_list_vm, ip_list_host, "The private IP addresses are wrong.\n"
            "Expect: {}\nReal: {}".format(ip_list_host, ip_list_vm))
        #tear down
        self.vm.delete(wait=True)
        self.vm.create(wait=True)
        self.vm.start(wait=True)
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)

    def test_cloudinit_login_with_publickey(self):
        """
        case_tag:
            cloudinit,cloudinit_tier1
        case_priority:
            1
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            VIRT-103831 - CLOUDINIT-TC: VM can successfully login after provisioning(with public key authentication)
        key_steps:        
        1. Create a VM with only public key authentication
        2. Login with publickey, should have sudo privilege
        """
        output=utils_lib.run_cmd(self, "whoami", expect_ret=0)
        self.assertEqual(
            self.vm.vm_username, output.rstrip('\n'),
            "Login VM with publickey error: output of cmd `whoami` unexpected -> %s"
            % output.rstrip('\n'))
        sudooutput=utils_lib.run_cmd(self, "sudo cat /etc/sudoers.d/90-cloud-init-users", expect_ret=0)
        self.assertIn(
            "%s ALL=(ALL) NOPASSWD:ALL" % self.vm.vm_username,
            sudooutput,
            "No sudo privilege")

    def test_cloudinit_datasource(self):        
        """
        case_tag:
            cloudinit,cloudinit_tier1
        case_priority:
            1
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-286739 - CLOUDINIT-TC: Check the datasource on openstack, aws, nutanix, Ali
        key_steps:        
        1. Launch instance with cloud-init installed
        2. Check the datasource is correct
        # cat /run/cloud-init/cloud.cfg
        """
        datasource={'openstack':'OpenStack',
                    'aws':'Ec2',
                    'nutanix':'ConfigDrive',
                    'Ali':'AliYun'}
        if self.vm.provider not in datasource.keys():
            self.skipTest('skip run as no such provider in datasource list')
        for provider,name in datasource.items():
            if self.vm.provider == provider:
                utils_lib.run_cmd(self,
                                  'cat /run/cloud-init/cloud.cfg',
                                  expect_ret=0,
                                  expect_kw='{}, None'.format(name),
                                  msg='check if the datasource is correct')
                utils_lib.run_cmd(self,
                                  'cat /run/cloud-init/ds-identify.log | grep datasource',
                                  expect_ret=0,
                                  expect_kw='Found single datasource: {}'.format(name),
                                  msg='check if found the datasource')

    def test_cloudinit_check_instance_data_json(self):         
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            bz#: 1744526
            RHEL-182312 - CLOUDINIT-TC:cloud-init can successfully write data to instance-data.json
        key_steps:        
        1. Launch instance with cloud-init installed
        2. Check instance-data.json
        """
        cmd = 'ls -l /run/cloud-init/instance-data.json'
        utils_lib.run_cmd(self,
                          cmd,
                          expect_ret=0,
                          expect_not_kw='No such file or directory',
                          msg='check /run/cloud-init/instance-data.json')

    def test_cloudinit_check_config_ipv6(self):        
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-189023 - CLOUDINIT-TC: check ipv6 configuration
        key_steps:        
        1. Launch instance with cloud-init installed
        2. Check there is dynamic IPv6 address
        Note: will add nm keyfiles configuration check after BZ2098624 is fixed
        """        
        cmd = "ip addr show | grep inet6 | grep 'scope global'"
        utils_lib.run_cmd(self,
                          cmd,
                          expect_ret=0,
                          expect_kw='scope global',
                          msg='check ipv6 scope global address')

    def test_cloudinit_check_random_password_len(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-189226 - CLOUDINIT-TC: checking random password and its length
        key_steps:
        """
        if self.vm.provider != 'openstack':
            self.skipTest('skip run as this needs to configure user-date, configured on openstack')
        #security check: random password only output to openstack console log, 
        #no password output in cloud-init-output.log and /var/log/messages
        cmd = 'sudo cat /var/log/messages'
        utils_lib.run_cmd(self, 
                          cmd, 
                          expect_ret=0,
                          expect_not_kw="the following 'random' passwords", 
                          msg='check /var/log/messages')
        cmd = 'cat /var/log/cloud-init-output.log'
        utils_lib.run_cmd(self, 
                          cmd, 
                          expect_ret=0,
                          expect_not_kw="the following 'random' passwords", 
                          msg='check /var/log/cloud-init-output.log')
        #check /var/log/cloud-init-output.log mode is 640 and group is adm
        cmd = 'ls -l /var/log/cloud-init-output.log '
        utils_lib.run_cmd(self, 
                          cmd, 
                          expect_ret=0,
                          expect_kw='-rw-r-----. 1 root adm', 
                          msg='cloud-init-output.log mode should be 640 and group adm')

        #get openstack console log
        status, output= self.vm.get_console_log()
        if status and output is not None:
            self.assertIn("the following 'random' passwords", output, "Failed to get random password from console log")
            output = output.split("cloud-user:",1)[1]
            randompass = output.split("\n",1)[0]
            self.log.info("Get the random password is:"+randompass)
            self.assertEqual(len(randompass), 20, "Random password length is not 20")
        else:
            self.fail("Failed to get console log")
           
    def test_cloudinit_check_runcmd(self):        
        """
        case_tag:
            cloudinit,cloudinit_tier1
        case_priority:
            1
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-186183 - CLOUDINIT-TC:runcmd module:execute commands
        key_steps:
        """
        if self.vm.provider != 'openstack':
            self.skipTest('skip run as this needs to configure user-date, configured on openstack')
        cmd = 'sudo cat /var/log/messages'
        utils_lib.run_cmd(self, 
                          cmd, 
                          expect_ret=0,
                          expect_kw=': hello today!', 
                          msg='runcmd executed successfully')

    def test_cloudinit_show_full_version(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-196547	- CLOUDINIT-TC: cloud-init version should show full specific version
        key_steps:
            cloud-init --version should show version and release
        """
        utils_lib.run_cmd(self, "cloud-init --version>/tmp/1 2>&1")
        output = utils_lib.run_cmd(self, "cat /tmp/1").rstrip('\n')
        package = utils_lib.run_cmd(self, "rpm -q cloud-init").rstrip('\n')
        cloudinit_path = utils_lib.run_cmd(self, "which cloud-init").rstrip('\n')
        expect = package.rsplit(".", 1)[0].replace("cloud-init-", cloudinit_path+' ')
        self.assertEqual(output, expect, 
            "cloud-init --version doesn't show full version. Real: {}, Expect: {}".format(output, expect))

    def test_check_hostkey_permissions(self):        
        """
        case_tag:
            cloudinit,cloudinit_tier1
        case_priority:
            1
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL7-103836 - CLOUDINIT-TC: Default configuration can regenerate sshd keypairs
            bz: 2013644
        key_steps:
            This auto case only check host key permissions
            expected:  
            $ ls -l /etc/ssh/ssh_host*.pub | awk '{print $1,$3,$4,$9}'
            -rw-r--r--. root root /etc/ssh/ssh_host_ecdsa_key.pub
            -rw-r--r--. root root /etc/ssh/ssh_host_ed25519_key.pub
            -rw-r--r--. root root /etc/ssh/ssh_host_rsa_key.pub
            $ ls -l /etc/ssh/ssh_host*key| awk '{print $1,$3,$4,$9}'
            -rw-r-----. root ssh_keys /etc/ssh/ssh_host_ecdsa_key
            -rw-r-----. root ssh_keys /etc/ssh/ssh_host_ed25519_key
            -rw-r-----. root ssh_keys /etc/ssh/ssh_host_rsa_key
        """
        self.log.info("check host key permissions")
        self.log.info("Public host key permissions should be 644 and owner/group should be root.")
        cmd = "ls -l /etc/ssh/ssh_host*.pub | awk '{print $1,$3,$4,$9}'"
        public_keys = utils_lib.run_cmd(self, cmd, msg='Get all public host keys').split('\n')
        for key in public_keys:
            if len(key) == 0:
                continue
            self.assertIn('-rw-r--r--. root root', key,
                    msg=" Unexpected permissions -> %s" % key)
        self.log.info("Private host key permissions should be 640 and owner/group should be root/ssh_keys.")
        cmd = "ls -l /etc/ssh/ssh_host*key | awk '{print $1,$3,$4,$9}'"
        private_keys = utils_lib.run_cmd(self, cmd, msg='Get all private host keys').split('\n')  
        for key in private_keys:
            if len(key) == 0:
                continue
            self.assertIn('-rw-r-----. root ssh_keys', key,
                    msg=" Unexpected permissions -> %s" % key)

    def test_check_cloudinit_fingerprints(self):        
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL7-103836 - CLOUDINIT-TC: Default configuration can regenerate sshd keypairs
            bz: 1957532
        key_steps:
            This auto case only check fingerprints is saved in /var/log/messages.
            expected:  
                # awk '/BEGIN/,/END/' /var/log/messages
                Sep 17 10:39:26 xiachen-testvm-rhel8 ec2[5447]: -----BEGIN SSH HOST KEY FINGERPRINTS-----
                Sep 17 10:39:26 xiachen-testvm-rhel8 ec2[5447]: 256 SHA256:USGMs+eQW403mILvsE5deVxZ2TC7IdQnUySEZFszlK4 root@xiachen-testvm-rhel8 (ECDSA)
                Sep 17 10:39:26 xiachen-testvm-rhel8 ec2[5447]: 256 SHA256:B/drC+5wa6xDhPaKwBNWj2Jw+lUsjpr8pEm67PG8HtM root@xiachen-testvm-rhel8 (ED25519)
                Sep 17 10:39:26 xiachen-testvm-rhel8 ec2[5447]: 3072 SHA256:6sCV1CusDhQzuoTO2FQFyyf9PmsclAd38zhkGs3HaUk root@xiachen-testvm-rhel8 (RSA)
                Sep 17 10:39:26 xiachen-testvm-rhel8 ec2[5447]: -----END SSH HOST KEY FINGERPRINTS-----
        """
        self.log.info("check fingerprints is saved in /var/log/messages")
        cmd = "sudo awk '/BEGIN/,/END/' /var/log/messages"
        out = utils_lib.run_cmd(self, cmd, msg='get fingerprints in /var/log/messages')
        # change 'SHA256' to ' SHA256' for exact match
        # change != to > for fault tolerance
        if out.count('BEGIN') > out.count(' SHA256')/3:
            self.fail('fingerprints count {} does not match expected {}'.format(out.count(' SHA256')/3,out.count('BEGIN')))

    def test_cloudinit_no_duplicate_swap(self):        
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-205128 - CLOUDINIT-TC: Can deal with the conflict of having swap configured 
            on /etc/fstab *and* having cloud-init duplicating this configuration automatically
        key_steps:
            1. Deploy a VM, attach an additional volume(or dd a file) to mkswap. 
            Add it to /etc/fstab, swapon, then check the free -m
            2. Configure cloud-init, /etc/cloud/cloud.cfg.d/cc_mount.cfg
            3. Use this VM as a template and create a new VM_new based on this VM
            4. Login VM_new and check /etc/fstab, no duplicate swap entry
        """
        utils_lib.run_cmd(self, "dd if=/dev/zero of=/tmp/swapfile01 bs=1M count=1024")
        utils_lib.run_cmd(self, "chmod 600 /tmp/swapfile01")
        utils_lib.run_cmd(self, "mkswap -L swap01 /tmp/swapfile01")
        cmd = 'echo "/tmp/swapfile01    swap    swap    defaults    0 0" >> /etc/fstab'
        utils_lib.run_cmd(self, "sudo bash -c '{}'".format(cmd))
        old_fstab = utils_lib.run_cmd(self, "cat /etc/fstab")
        utils_lib.run_cmd(self, "sudo swapon -a")
        old_swap = utils_lib.run_cmd(self, "free -m|grep Swap|awk '{print $2}'").rstrip('\n')

        cmd = 'echo -e "mounts:\n  - ["/tmp/swapfile01"]" > /etc/cloud/cloud.cfg.d/cc_mount.cfg'
        utils_lib.run_cmd(self, "sudo bash -c '{}'".format(cmd))
        utils_lib.run_cmd(self, "sudo rm -rf /var/lib/cloud/instance/sem")
        utils_lib.run_cmd(self, "sudo cloud-init single --name cc_mounts")
        utils_lib.run_cmd(self, "sudo swapoff -a")
        utils_lib.run_cmd(self, "sudo swapon -a")
        new_swap = utils_lib.run_cmd(self, "free -m|grep Swap|awk '{print $2}'").rstrip('\n')
        new_fstab = utils_lib.run_cmd(self, "cat /etc/fstab")
        # clean the swap config
        utils_lib.run_cmd(self, "sudo swapoff -a")
        utils_lib.run_cmd(self, "sudo rm -rf /etc/cloud/cloud.cfg.d/cc_mount.cfg")
        utils_lib.run_cmd(self, "sudo sed -i '/swapfile01/d' /etc/fstab")
        utils_lib.run_cmd(self, "sudo rm -rf /tmp/swapfile01")
        #utils_lib.run_cmd(self, "exit")
        self.assertNotEqual(old_swap, '0',
            "Swap size is 0 before cloud-init config")
        self.assertEqual(old_swap, new_swap,
            "Swap size is not same before and after cloud-init config")
        self.assertEqual(old_fstab, new_fstab,
            "The /etc/fstab is not same before and after cloud-init config")

    def _verify_authorizedkeysfile(self, keyfiles):
        # 1. Modify /etc/ssh/sshd_config
        utils_lib.run_cmd(self, 
            "sudo sed -i 's/^AuthorizedKeysFile.*$/AuthorizedKeysFile {}/g' /etc/ssh/sshd_config".format(keyfiles.replace('/', '\/')))
        utils_lib.run_cmd(self, 
                          "sudo grep '{}' /etc/ssh/sshd_config".format(keyfiles),
                          expect_ret=0,
                          expect_kw=keyfiles, 
                          msg='Check if change sshd_config successful')
        utils_lib.run_cmd(self, "sudo systemctl restart sshd")
        # 2. Remove cc_ssh flag and authorized_keys
        utils_lib.run_cmd(self, 
            "sudo rm -f /var/lib/cloud/instance/sem/config_ssh /home/{}/.ssh/authorized_keys".format(self.vm.vm_username))
        utils_lib.run_cmd(self, "sudo rm -rf {}".format(keyfiles))
        # 3. Run module ssh
        utils_lib.run_cmd(self, "sudo cloud-init single -n ssh")
        # 4. Verify can login
        utils_lib.init_connection(self, timeout=20)
        output=utils_lib.run_cmd(self, "whoami", expect_ret=0)
        self.assertEqual(
            self.vm.vm_username, output.rstrip('\n'),
            "Verify can login")

    def test_cloudinit_verify_multiple_files_in_authorizedkeysfile(self):        
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-189026	CLOUDINIT-TC: Verify multiple files in AuthorizedKeysFile
        key_steps:
            1. Launch VM/instance with cloud-init. Modify /etc/ssh/sshd_config:
            AuthorizedKeysFile .ssh/authorized_keys /etc/ssh/userkeys/%u
            2. Remove cc_ssh module flag and authorized_keys
            3. Run module ssh
            # cloud-init single -n ssh
            4. Verify can login successful and AuthorizedKeysFile has correct authority
            5. Set customized keyfile at the front:
            AuthorizedKeysFile /etc/ssh/userkeys/%u.ssh/authorized_keys
            Restart sshd service and rerun step2-4
        """
        # AuthorizedKeysFile .ssh/authorized_keys /etc/ssh/userkeys/%u
        self._verify_authorizedkeysfile(
            ".ssh/authorized_keys /etc/ssh/userkeys/%u")
        # Check the AuthorizedKeysFile authority is correct
        self.assertEqual(
            "-rw-------.",
            utils_lib.run_cmd(self, 
                "ls -al /home/%s/.ssh/authorized_keys | awk '{print $1}'" %(self.vm.vm_username)).rstrip('\n'),
            "The authority of the AuthorizedKeysFile is wrong!")
        self.assertEqual(
            self.vm.vm_username,
            utils_lib.run_cmd(self, 
                "ls -al /home/%s/.ssh/authorized_keys | awk '{print $3}'" %(self.vm.vm_username)).rstrip('\n'),
            "The owner of the AuthorizedKeysFile is wrong!")
        # AuthorizedKeysFile /etc/ssh/userkeys/%u .ssh/authorized_keys
        self._verify_authorizedkeysfile(
            "/etc/ssh/userkeys/%u .ssh/authorized_keys")
        # Check the AuthorizedKeysFile authority is correct
        self.assertEqual(
            "-rw-------.",
            utils_lib.run_cmd(self, 
                "ls -al /etc/ssh/userkeys/%s | awk '{print $1}'" %(self.vm.vm_username)).rstrip('\n'),
            "The authority of the AuthorizedKeysFile is wrong!")
        self.assertEqual(
            self.vm.vm_username,
            utils_lib.run_cmd(self, 
                "ls -al /etc/ssh/userkeys/%s | awk '{print $3}'" %(self.vm.vm_username)).rstrip('\n'),
            "The owner of the AuthorizedKeysFile is wrong!")
        # Recover the config to default: AuthorizedKeysFile .ssh/authorized_keys               
        self._verify_authorizedkeysfile(".ssh/authorized_keys")

    def test_cloudinit_verify_customized_file_in_authorizedkeysfile(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-189027	CLOUDINIT-TC: Verify customized file in AuthorizedKeysFile
            bz1862967
        key_steps:
            1. Launch VM/instance with cloud-init. Modify /etc/ssh/sshd_config:
            AuthorizedKeysFile .ssh/authorized_keys2
            2. Remove cc_ssh module flag and authorized_keys
            3. Run module ssh
            # cloud-init single -n ssh
            4. Verify can login successfully and AuthorizedKeysFile has correct authority
        """
        cloudinit_ver = utils_lib.run_cmd(self, "rpm -q cloud-init").rstrip('\n')        
        cloudinit_ver = float(re.search('cloud-init-(\d+.\d+)-', cloudinit_ver).group(1))
        if cloudinit_ver < 21.1:
            self.skipTest('skip run as this case is suitable for rhel higher than rhel-8.5 and rhel-9.0, bz1862967')
        self.log.info(
            "RHEL-189027 CLOUDINIT-TC: Verify customized file in AuthorizedKeysFile")
        self._verify_authorizedkeysfile(".ssh/authorized_keys2")
        # Check the AuthorizedKeysFile authority is correct
        self.assertEqual(
            "-rw-------.",
            utils_lib.run_cmd(self,
                "ls -al /home/%s/.ssh/authorized_keys2 | awk '{print $1}'" %(self.vm.vm_username)).rstrip('\n'),
            "The authority of the AuthorizedKeysFile is wrong!")
        self.assertEqual(
            self.vm.vm_username,
            utils_lib.run_cmd(self,
                "ls -al /home/%s/.ssh/authorized_keys2 | awk '{print $3}'" %(self.vm.vm_username)).rstrip('\n'),
            "The owner of the AuthorizedKeysFile is wrong!")        
        # Recover the config to default: AuthorizedKeysFile .ssh/authorized_keys
        # Remove ~/.ssh and check the permissions of the directory
        utils_lib.run_cmd(self,
            "sudo rm -rf /home/{}/.ssh".format(self.vm.vm_username))
        self._verify_authorizedkeysfile(".ssh/authorized_keys")
        # Check ~/.ssh authority is correct, bug 1995840
        self.assertEqual(
            "drwx------. cloud-user cloud-user",
            utils_lib.run_cmd(self,
                "ls -ld /home/%s/.ssh | awk '{print $1,$3,$4}'" %(self.vm.vm_username)).rstrip('\n'),
            "The authority .ssh is wrong!")

    def test_cloudinit_check_NOZEROCONF(self):       
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-152730 - CLOUDINIT-TC: Check 'NOZEROCONF=yes' in /etc/sysconfig/network
            cannot be removed by cloud-init
        key_steps:
            1. Create a VM with rhel-guest-image
            2. Login and check /etc/sysconfig/network
            3. There is "NOZEROCONF=yes" in /etc/sysconfig/network
        """
        self.log.info(
            "RHEL-152730 - CLOUDINIT-TC: Check 'NOZEROCONF=yes' in /etc/sysconfig/network")
        cmd = 'sudo cat /etc/sysconfig/network'
        utils_lib.run_cmd(self,
                          cmd,
                          expect_ret=0,
                          expect_kw='NOZEROCONF=yes',
                          msg='check if NOZEROCONF=yes in /etc/sysconfig/network')

    def test_cloudinit_root_exit_code(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-287348 - CLOUDINIT-TC: Using root user error should 
            cause a non-zero exit code
        key_steps:
            1. Launch instance with cloud-init installed
            2. Check the /root/.ssh/authorized_keys, the exit code is 142
            # cat /root/.ssh/authorized_keys" 
        """
        if self.vm.provider == 'nutanix':
            self.skipTest('skip run for nutanix platform on which authorized_keys be modified.')
        self.log.info(
            "RHEL-287348 - CLOUDINIT-TC: Using root user error should cause a non-zero exit code")
        cmd = 'sudo cat /root/.ssh/authorized_keys'
        utils_lib.run_cmd(self,
                          cmd,
                          expect_ret=0,
                          expect_kw='echo;sleep 10;exit 142',
                          msg='check if the exit code correct')

    def test_cloudinit_ip_route_append(self):        
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-288020 - CLOUDINIT-TC: Using "ip route append" 
            when config static ip route via cloud-init
        key_steps:
            1. Launch instance with cloud-init installed on OpenStack PSI
            2. Check /var/log/cloud-init.log
            cloud-init should config static ip route via "ip route append" 
        """
        if self.vm.provider == 'nutanix':
            self.skipTest('skip run for nutanix platform on which there is no ip route append command')
        self.log.info(
            "RHEL-288020 - CLOUDINIT-TC: Check ip route append when config static ip route")
        cmd = 'cat /var/log/cloud-init.log | grep append'

        utils_lib.run_cmd(self,
                          cmd,
                          expect_ret=0,
                          expect_kw="Running command \['ip', '-4', 'route', 'append',",
                          msg="check if using ip route append")

    def test_cloudinit_dependency(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-288482 - CLOUDINIT-TC: Check cloud-init dependency, openssl and gdisk
        key_steps:
            1. Launch instance with cloud-init installed
            2. Check the cloud-init denpendency
            # rpm -qR cloud-init 
        """
        self.log.info(
            "RHEL-288482 - CLOUDINIT-TC: Check cloud-init dependency, openssl and gdisk")       
        dep_list = 'openssl,gdisk'
        cmd = 'sudo rpm -qR cloud-init'
        utils_lib.run_cmd(self,
                          cmd,
                          expect_ret=0,
                          expect_kw='%s' % dep_list,
                          msg='check if %s are cloud-init dependency' % dep_list)

    def test_cloudinit_removed_dependency(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-198795 - CLOUDINIT-TC: Check cloud-init removed dependency,
            net-tools, python3-mock, python3-nose, python3-tox
        key_steps:
            1. Launch instance with cloud-init installed
            2. Check the cloud-init denpendency
            # rpm -qR cloud-init
        """
        self.log.info(
            "RHEL-198795 - CLOUDINIT-TC: Check cloud-init removed dependency")
        rm_dep_list = 'net-tools,python3-mock,python3-nose,python3-tox'
        cmd = 'sudo rpm -qR cloud-init'
        utils_lib.run_cmd(self,
                          cmd,
                          expect_ret=0,
                          expect_not_kw='%s' % rm_dep_list,
                          msg='check if %s are removed from cloud-init dependency' % rm_dep_list)

    def _check_cloudinit_done_and_service_isactive(self):
        # if cloud-init status is running, waiting
        cmd = 'sudo cloud-init status'
        output=utils_lib.run_cmd(self, cmd).rstrip('\n')
        while output=='status: running':
            time.sleep(20) # waiting for cloud-init done
            output = utils_lib.run_cmd(self, cmd).rstrip('\n')        
        # check cloud-init status is done        
        utils_lib.run_cmd(self, cmd, expect_ret=0, expect_kw='status: done', msg='Get cloud-init status')
        # check cloud-init services status are active
        service_list = ['cloud-init-local',
                        'cloud-init',
                        'cloud-config',
                        'cloud-final']
        for service in service_list:
            cmd = "sudo systemctl is-active %s" % service
            utils_lib.run_cmd(self, cmd, expect_ret=0, expect_kw='active', msg = "check %s status" % service)

    def test_cloudinit_create_vm_config_drive(self):        
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-189225 - CLOUDINIT-TC: launch vm with config drive
        key_steps:
            basic case of config drive
            1. Create a VM with datasource 'Config Drive'
            2. Login and check user sudo privilege
            3. check data source in /run/cloud-init/cloud.cfg
        """
        if self.vm.provider != 'openstack':
            self.skipTest('skip run as this is openstack specific case')
        self.log.info(
            "RHEL-189225 - CLOUDINIT-TC: launch vm with config drive")        
        if self.vm.exists():
            self.vm.delete()
            time.sleep(30)
        self.vm.config_drive = True
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)
        output = utils_lib.run_cmd(self, 'whoami').rstrip('\n')
        self.assertEqual(
            self.vm.vm_username, output,
            "Login VM with publickey error: output of cmd `whoami` unexpected -> %s"
            % output)
        sudooutput=utils_lib.run_cmd(self, "sudo cat /etc/sudoers.d/90-cloud-init-users", expect_ret=0) 
        self.assertIn(
            "%s ALL=(ALL) NOPASSWD:ALL" % self.vm.vm_username,
            sudooutput,
            "No sudo privilege")
        cmd = 'sudo cat /run/cloud-init/cloud.cfg'
        utils_lib.run_cmd(self,
                          cmd,
                          expect_ret=0,
                          expect_kw='ConfigDrive',
                          msg='check if ConfigDrive in /run/cloud-init/cloud.cfg')
        # check cloud-init status is done and services are active
        self._check_cloudinit_done_and_service_isactive()
        #teardown        
        self.vm.delete()
        self.vm.config_drive = None
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)

    def test_cloudinit_login_with_password_userdata(self):
        """
        case_tag:
            cloudinit,cloudinit_tier1
        case_priority:
            1
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL7-103830 - CLOUDINIT-TC: VM can successfully login
            after provisioning(with password authentication)
        key_steps:
            1. Create a VM with only password authentication
            2. Login with password, should have sudo privilege
        """     
        self.log.info(
            "RHEL7-103830 - CLOUDINIT-TC: VM can login with password authentication")
        if self.vm.exists():
            self.vm.delete()
            time.sleep(30)
        save_userdata = self.vm.user_data
        save_keypair = self.vm.keypair
        self.vm.user_data = """\
#cloud-config

user: {0}
password: {1}
chpasswd: {{ expire: False }}
ssh_pwauth: 1
""".format(self.vm.vm_username, self.vm.vm_password)       
        self.vm.keypair = None
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        test_login = utils_lib.send_ssh_cmd(self.vm.floating_ip, self.vm.vm_username, self.vm.vm_password, "whoami")
        self.assertEqual(self.vm.vm_username,
                         test_login[1].strip(),
                         "Fail to login with password: %s" % format(test_login[1].strip()))        
        test_sudo = utils_lib.send_ssh_cmd(self.vm.floating_ip, self.vm.vm_username, self.vm.vm_password, "sudo cat /etc/sudoers.d/90-cloud-init-users")
        self.assertIn("%s ALL=(ALL) NOPASSWD:ALL" % self.vm.vm_username,
                         test_sudo[1].strip(),
                         "No sudo privilege")
        #teardown        
        self.vm.delete()
        self.vm.keypair = save_keypair
        self.vm.user_data = save_userdata
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)

    def _reboot_inside_vm(self):       
        before = utils_lib.run_cmd(self, 'last reboot --time-format full')
        utils_lib.run_cmd(self, 'sudo reboot')
        time.sleep(10)
        utils_lib.init_connection(self, timeout=self.timeout)
        output = utils_lib.run_cmd(self, 'whoami')
        self.assertEqual(
            self.vm.vm_username, output.strip(),
            "Reboot VM error: output of cmd `who` unexpected -> %s" % output)
        after = utils_lib.run_cmd(self, 'last reboot --time-format full')
        self.assertNotEqual(
            before, after,
            "Reboot VM error: before -> %s; after -> %s" % (before, after))

    def test_cloudinit_check_resolv_conf_reboot(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-196518 - CLOUDINIT-TC: check dns configuration on openstack instance
            RHEL-182309 - CLOUDINIT-TC: /etc/resolv.conf will not lose config after reboot
        key_steps:
            1. check dns configuration in /etc/resolv.conf
            2. check /etc/NetworkManager/conf.d/99-cloud-init.conf
            3. run hostnamectl command and then check resolv.conf again
            4. reboot
            5. Check /etc/resolv.conf
        """ 
        cmd = 'cat /etc/resolv.conf'
        utils_lib.run_cmd(self,
                          cmd,
                          expect_ret=0,
                          expect_kw='nameserver',
                          msg='check if there is dns information in /etc/resolv.conf')
        #get network dns information
        output = utils_lib.run_cmd(self, 'cloud-init query ds.network_json.services').rstrip('\n')
        services = json.loads(output)
        for service in services:
            expect_dns_addr=service.get("address")
            utils_lib.run_cmd(self,
                           cmd,
                           expect_ret=0,
                           expect_kw=expect_dns_addr,
                           msg='check dns configuration %s in /etc/resolv.conf' % expect_dns_addr)
        cmd2 = 'cat /etc/NetworkManager/conf.d/99-cloud-init.conf'
        utils_lib.run_cmd(self,
                          cmd2,
                          expect_ret=0,
                          expect_kw='dns = none',
                          msg='check dns configuration of NM')
        utils_lib.run_cmd(self, 'cp /etc/resolv.conf  ~/resolv_bak.conf')
        cmd1 = 'sudo hostnamectl set-hostname host1.test.domain'                  
        utils_lib.run_cmd(self, cmd1, expect_ret=0, msg='set hostname')
        diff = utils_lib.run_cmd(self, "diff ~/resolv_bak.conf /etc/resolv.conf").rstrip('\n')
        self.assertEqual(diff, '', 
            "After setting hostname, resolv.conf is changed:\n"+diff)
        self._reboot_inside_vm()
        diff = utils_lib.run_cmd(self, "diff ~/resolv_bak.conf /etc/resolv.conf").rstrip('\n')
        self.assertEqual(diff, '', 
            "After reboot, resolv.conf is changed:\n"+diff)

    def _get_service_startup_time(self, servicename):
        output = utils_lib.run_cmd(self, "sudo systemd-analyze blame | grep %s | awk '{print $1}'" % servicename).rstrip('\n')
        if 'ms' in output:
            return 1
        if 'min' in output:
            boot_time_min = re.findall('[0-9]+min', output)[0]
            boot_time_min = boot_time_min.strip('min')
            boot_time_sec = int(boot_time_min) * 60
            return boot_time_sec
        service_time_sec = output.strip('s')
        return service_time_sec

    def test_cloudinit_boot_time(self):        
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-189580 - CLOUDINIT-TC: Check VM first launch boot time and cloud-init startup time
        key_steps:
            1. Launch a VM with cloud-init installed
            2. Login VM on the VM first boot
            3. Check boot time and cloud-init services startup time
            # systemd-analyze
            # systemd-analyze blame
            4. The boot time should be less than 50s, cloud-init services startup time should less than 18s
        """
        self.log.info(
            "RHEL-189580 - CLOUDINIT-TC: Check VM first launch boot time and cloud-init startup time")
        max_boot_time = 60
        cloud_init_startup_time = 20
        if self.vm.exists():
            self.vm.delete()
            time.sleep(30)
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)
        # check cloud-init status is done and services are active
        self._check_cloudinit_done_and_service_isactive()
        # Check boot time
        boot_time_sec = utils_lib.getboottime(self)
        self.assertLess(
            float(boot_time_sec), float(max_boot_time), 
            "First boot time is greater than {}".format(max_boot_time))        
        # Check cloud-init services time
        service_list = ['cloud-init-local.service',
                        'cloud-init.service',
                        'cloud-config.service',
                        'cloud-final.service']
        for service in service_list:
            service_time_sec = self._get_service_startup_time("%s" % service)
            self.assertLess(
                float(service_time_sec), float(cloud_init_startup_time), 
                "{0} startup time is greater than {1}".format(service, cloud_init_startup_time))

    def test_cloudinit_reboot_time(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-282359 - CLOUDINIT-TC: Check VM subsequent boot time and cloud-init startup time
        key_steps:
            1. Launch a VM with cloud-init installed
            2. Login VM and reboot VM
            3. Check reboot time and cloud-init services startup time
            # systemd-analyze
            # systemd-analyze blame
            4. The reboot time should be less than 30s, cloud-init services startup time should less than 5s
        """
        self.log.info(
            "RHEL-282359 - CLOUDINIT-TC: Check VM subsequent boot time and cloud-init startup time")
        max_boot_time = 30
        cloud_init_startup_time = 5
        # Reboot VM
        self._reboot_inside_vm()
        # Check boot time
        boot_time_sec = utils_lib.getboottime(self)
        self.assertLess(
            float(boot_time_sec), float(max_boot_time), 
            "First boot time is greater than {}".format(max_boot_time))
        # Check cloud-init services time
        service_list = ['cloud-init-local.service',
                        'cloud-init.service',
                        'cloud-config.service',
                        'cloud-final.service']
        for service in service_list:
            service_time_sec = self._get_service_startup_time("%s" % service)
            self.assertLess(
                float(service_time_sec), float(cloud_init_startup_time), 
                "{0} startup time is greater than {1}".format(service, cloud_init_startup_time))

    def test_cloudinit_disable_cloudinit(self):        
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-287483: CLOUDINIT-TC: cloud-init dhclient-hook script shoud exit
            while cloud-init services are disabled
        key_steps:
            1. Install cloud-init package in VM, disable cloud-init and related services:
               # systemctl disable cloud-{init-local,init,config,final}
            2. Clean the VM and reboot VM
            3. Check the VM status after reboot
            The cloud-init should not run , and the related services are disabled
            4. Recover the VM config(enable cloud-init), reboot VM, check the cloud-init is enabled
        """
        self.log.info("RHEL-287483: CLOUDINIT-TC: check cloud-init disable")
        # Disable cloud-init
        utils_lib.run_cmd(self, "sudo systemctl disable cloud-{init-local,init,config,final}")
        time.sleep(1)
        self.assertNotIn("enabled",
                    utils_lib.run_cmd(self, "sudo systemctl is-enabled cloud-{init-local,init,config,final}"),
                    "Fail to disable cloud-init related services")
        # Clean the VM
        utils_lib.run_cmd(self, "sudo rm -rf /var/lib/cloud /var/log/cloud-init* \
            /var/log/messages /run/cloud-init")    
        # Reboot VM
        self._reboot_inside_vm()        
        # Check the new VM status
        self.assertNotIn("enabled",
                    utils_lib.run_cmd(self, "sudo systemctl is-enabled cloud-{init-local,init,config,final}"),
                    "Fail to disable cloud-init related services!")
        self.assertIn("status: not run",
                    utils_lib.run_cmd(self, "sudo cloud-init status"),
                    "cloud-init status is wrong!")
        self.assertIn("inactive",
                    utils_lib.run_cmd(self, "sudo systemctl is-active cloud-init-local"),
                    "cloud-init-local service status is wrong!")
        # Recover the VM config
        utils_lib.run_cmd(self, "sudo systemctl enable cloud-{init-local,init,config,final}")
        time.sleep(1)
        # Reboot VM
        self._reboot_inside_vm()
        # Check the VM status
        self.assertNotIn("disabled",
                    utils_lib.run_cmd(self, "sudo systemctl is-enabled cloud-{init-local,init,config,final}"),
                    "Fail to disable cloud-init related services!")
        #teardown        
        self.vm.delete()
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)

    def test_cloudinit_create_vm_two_nics(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-186186 - CLOUDINIT-TC: launch an instance with 2 interfaces
            basic case of two nics, the second nic is default ipv6 mode slaac
        key_steps:
            1. Create a VM with two nics
            2. Login and check user
            3. check network config file
        """
        if self.vm.provider != 'openstack':
            self.skipTest('skip run as this case is openstack specific which using openstack PSI NIC uuid')
        self.log.info(
            "RHEL-186186 - CLOUDINIT-TC: launch an instance with 2 interfaces")
        # the second nic using hard code? (the second network only contains ipv6, network name provider_net_ipv6_only, ipv6 slaac)
        # if the second nic has ipv4, the ssh login may select it but it could not be connected
        # this solution ensure ssh using eth0 ipv4
        self.vm.second_nic_id = "10e45d6d-5924-48ee-9f5a-9713f5facc36"
        if self.vm.exists():
            self.vm.delete()
            time.sleep(30)
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)
        output = utils_lib.run_cmd(self, 'whoami').rstrip('\n')
        self.assertEqual(
            self.vm.vm_username, output,
            "Login VM with publickey error: output of cmd `whoami` unexpected -> %s"
            % output)
        cmd = 'ip addr show eth1'
        utils_lib.run_cmd(self, cmd, expect_ret=0, expect_kw=',UP,')
        cloudinit_ver = utils_lib.run_cmd(self, "rpm -q cloud-init").rstrip('\n')        
        cloudinit_ver = float(re.search('cloud-init-(\d+.\d+)-', cloudinit_ver).group(1))
        if cloudinit_ver < 22.1:
            cmd = 'sudo cat /etc/sysconfig/network-scripts/ifcfg-eth1'
            utils_lib.run_cmd(self, cmd, expect_ret=0, expect_kw='DEVICE=eth1')
        else:
            cmd = 'sudo cat /etc/NetworkManager/system-connections/cloud-init-eth1.nmconnection'
            utils_lib.run_cmd(self, cmd, expect_ret=0, expect_kw='id=cloud-init eth1')
        # check cloud-init status is done and services are active
        self._check_cloudinit_done_and_service_isactive()
        #teardown        
        self.vm.delete()
        self.vm.second_nic_id = None
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)

    def test_cloudinit_create_vm_stateless_ipv6(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-186180 - CLOUDINIT-TC: correct config for dhcp-stateless openstack subnets
        key_steps:
            1. Create a VM with two nics, the second nic is stateless ipv6 mode
            2. Login and check user
            3. check network config file
        """
        if self.vm.provider != 'openstack':
            self.skipTest('skip run as this case is openstack specific')
        self.log.info(
            "RHEL-186180 - CLOUDINIT-TC: correct config for dhcp-stateless openstack subnets")
        # the second nic using hard code?  (net-ipv6-stateless, only subnet ipv6, dhcp-stateless)
        self.vm.second_nic_id = "e66c7343-98d6-4f07-9d64-2b8bb31d7df8"
        if self.vm.exists():
            self.vm.delete()
            time.sleep(30)
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)
        output = utils_lib.run_cmd(self, 'whoami').rstrip('\n')
        self.assertEqual(
            self.vm.vm_username, output,
            "Login VM with publickey error: output of cmd `whoami` unexpected -> %s"
            % output)
        # change command to ip addr because of no net-tool by default in rhel8.4
        cmd = 'ip addr show eth1'
        utils_lib.run_cmd(self, cmd, expect_ret=0, expect_kw=',UP,')
        cloudinit_ver = utils_lib.run_cmd(self, "rpm -q cloud-init").rstrip('\n')        
        cloudinit_ver = float(re.search('cloud-init-(\d+.\d+)-', cloudinit_ver).group(1))
        if cloudinit_ver < 22.1:
            cmd = 'sudo cat /etc/sysconfig/network-scripts/ifcfg-eth1'
            utils_lib.run_cmd(self, cmd, expect_ret=0, expect_kw='DHCPV6C_OPTIONS=-S,IPV6_AUTOCONF=yes')
        # Will add NM keyfile check after BZ 2098501 fix
        # check cloud-init status is done and services are active
        self._check_cloudinit_done_and_service_isactive()
        #teardown        
        self.vm.delete()
        self.vm.second_nic_id = None
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)

    def test_cloudinit_create_vm_stateful_ipv6(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-186181 - CLOUDINIT-TC: correct config for dhcp-stateful openstack subnets
        key_steps:
            1. Create a VM with two nics, the second nic is dhcp-stateful ipv6 mode
            2. Login and check user
            3. check network config file
        """
        if self.vm.provider != 'openstack':
            self.skipTest('skip run as this case is openstack specific')
        self.log.info(
            "RHEL-186181 - CLOUDINIT-TC: correct config for dhcp-stateful openstack subnets")
        # the second nic using hard code? (net-ipv6-stateful, only subnet ipv6, dhcp-stateful)
        self.vm.second_nic_id = "9b57a458-5c76-4e4e-b6bf-f1e01388a3b4"
        if self.vm.exists():
            self.vm.delete()
            time.sleep(30)
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)
        output = utils_lib.run_cmd(self, 'whoami').rstrip('\n')
        self.assertEqual(
            self.vm.vm_username, output,
            "Login VM with publickey error: output of cmd `whoami` unexpected -> %s"
            % output)
        cmd = 'ip addr show eth1'
        utils_lib.run_cmd(self, cmd, expect_ret=0, expect_kw=',UP,')
        cloudinit_ver = utils_lib.run_cmd(self, "rpm -q cloud-init").rstrip('\n')        
        cloudinit_ver = float(re.search('cloud-init-(\d+.\d+)-', cloudinit_ver).group(1))
        if cloudinit_ver < 22.1:
            cmd = 'sudo cat /etc/sysconfig/network-scripts/ifcfg-eth1'
            utils_lib.run_cmd(self, cmd, expect_ret=0, expect_kw='IPV6_FORCE_ACCEPT_RA=yes')
        # Will add NM keyfile check after BZ 2098501 fix
        # check cloud-init status is done and services are active
        self._check_cloudinit_done_and_service_isactive()
        #teardown        
        self.vm.delete()
        self.vm.second_nic_id = None
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)

    def test_cloudinit_auto_install_package_with_subscription_manager(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-186182	CLOUDINIT-TC:auto install package with subscription manager
        key_steps:
            1. Add content to user data config file
            rh_subscription:
            username: ******
            password: ******
            auto-attach: True
            packages:
            - dos2unix
            2. create VM
            3. Verify register with subscription-manager and install package by cloud-init successfully
        """
        if self.vm.provider != 'openstack' and self.vm.provider != 'nutanix':
            self.skipTest('skip run as this case need connect rhsm stage server, not suitable for public cloud')
        self.log.info("RHEL-186182 CLOUDINIT-TC:auto install package with subscription manager")
        if self.vm.exists():
            self.vm.delete()
            time.sleep(30)
        package = "dos2unix"        
        save_userdata = self.vm.user_data
        self.vm.user_data = """\
#cloud-config

rh_subscription:
  username: {0}
  password: {1}
  rhsm-baseurl: {2}
  server-hostname: {3}
  auto-attach: true
  disable-repo: []
packages:
  - {4}
""".format(self.vm.subscription_username, self.vm.subscription_password, 
    self.vm.subscription_baseurl, self.vm.subscription_serverurl, package)
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)
        # check login
        output = utils_lib.run_cmd(self, 'whoami').rstrip('\n')
        self.assertEqual(
            self.vm.vm_username, output,
            "Create VM error: output of cmd `who` unexpected -> %s" % output)
        self.log.info("Waiting 30s for subscription-manager done...")
        time.sleep(30) # waiting for subscription-manager register done.
        # no error because of disable-repo null
        # check cloud-init status is done and services are active
        self._check_cloudinit_done_and_service_isactive()
        # check register
        cmd = "sudo grep 'Registered successfully' /var/log/cloud-init.log"
        utils_lib.run_cmd(self,
                    cmd,
                    expect_ret=0,
                    expect_kw='Registered successfully',
                    msg='No Registered successfully log in cloud-init.log')
        cmd = "sudo subscription-manager identity"
        utils_lib.run_cmd(self,
                    cmd,
                    expect_ret=0,
                    msg='Fail to register with subscription-manager')
        # check auto-attach
        output = utils_lib.run_cmd(self, "sudo subscription-manager list --consumed --pool-only").rstrip('\n')
        self.assertNotEqual("", output, "Cannot auto-attach pools")
        # check package installed
        time.sleep(30) # waiting for package install done.
        cmd = "rpm -q {}".format(package)
        utils_lib.run_cmd(self,
                    cmd,
                    expect_ret=0,
                    expect_kw='{}'.format(package),
                    msg="Fail to install package {} by cloud-init".format(package))
        #teardown        
        self.vm.delete()
        self.vm.user_data = save_userdata
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)

    def test_cloudinit_verify_rh_subscription_enablerepo_disablerepo(self):
        """
        case_tag:
            cloudinit,cloudinit_tier2
        case_priority:
            2
        component:
            cloud-init
        maintainer:
            huzhao@redhat.com
        description:
            RHEL-189134 - CLOUDINIT-TC: Verify rh_subscription enable-repo and disable-repo
        key_steps:
            1. Add content to user data config file
            rh_subscription:
            username: ******
            password: ******
            auto-attach: True
            enable-repo: ['rhel-*-baseos-*rpms','rhel-*-supplementary-*rpms']
            disable-repo: ['rhel-*-appstream-*rpms']
            2. create VM
            3. Verify register with subscription-manager and enabled repos and disabled repos successfully
        """
        if self.vm.provider != 'openstack' and self.vm.provider != 'nutanix':
            self.skipTest('skip run as this case need connect rhsm stage server, not suitable for public cloud')
        rhel_ver = utils_lib.run_cmd(self, "sudo cat /etc/redhat-release").rstrip('\n')
        rhel_ver = float(re.search('release\s+(\d+.\d+)\s+', rhel_ver).group(1))
        if rhel_ver >= 9.0 or rhel_ver < 8.0:
            self.skipTest('skip run as this case is only test rhel-8')        
        self.log.info("RHEL-189134 - CLOUDINIT-TC: Verify rh_subscription enable-repo and disable-repo")
        if self.vm.exists():
            self.vm.delete()
            time.sleep(30)
        save_userdata = self.vm.user_data
        self.vm.user_data = """\
#cloud-config

rh_subscription:
  username: {0}
  password: {1}
  rhsm-baseurl: {2}
  server-hostname: {3}
  auto-attach: true
  enable-repo: ['rhel-8-for-x86_64-baseos-beta-rpms','rhel-8-for-x86_64-supplementary-beta-rpms']
  disable-repo: ['rhel-8-for-x86_64-appstream-beta-rpms']
""".format(self.vm.subscription_username, self.vm.subscription_password, 
    self.vm.subscription_baseurl, self.vm.subscription_serverurl)
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)
        # check login
        output = utils_lib.run_cmd(self, 'whoami').rstrip('\n')
        self.assertEqual(
            self.vm.vm_username, output,
            "Reboot VM error: output of cmd `who` unexpected -> %s" % output)
        # waiting for subscription-manager register done.
        # 51.55900s (modules-config/config-rh_subscription)
        self.log.info("Waiting 60s for subscription-manager done...")
        time.sleep(60) 
        # check cloud-init status is done and services are active
        self._check_cloudinit_done_and_service_isactive()
        # check register
        cmd = "sudo grep 'Registered successfully' /var/log/cloud-init.log"
        utils_lib.run_cmd(self,
                    cmd,
                    expect_ret=0,
                    expect_kw='Registered successfully',
                    msg='No Registered successfully log in cloud-init.log')
        cmd = "sudo subscription-manager identity"
        utils_lib.run_cmd(self,
                    cmd,
                    expect_ret=0,
                    msg='Fail to register with subscription-manager')
        # check auto-attach
        output = utils_lib.run_cmd(self, "sudo subscription-manager list --consumed --pool-only").rstrip('\n')
        self.assertNotEqual("", output, "Cannot auto-attach pools")
        # check enabled/disabled repos
        enable_repo_1 = 'rhel-8-for-x86_64-baseos-beta-rpms'
        enable_repo_2 = 'rhel-8-for-x86_64-supplementary-beta-rpms'
        disable_repo = 'rhel-8-for-x86_64-appstream-beta-rpms'
        repolist = utils_lib.run_cmd(self, "yum repolist|awk '{print $1}'").split('\n')
        self.assertIn(enable_repo_1, repolist,
            "Repo of {} is not enabled".format(enable_repo_1))
        self.assertIn(enable_repo_2, repolist,
            "Repo of {} is not enabled".format(enable_repo_2))
        self.assertNotIn(disable_repo, repolist,
            "Repo of {} is not disabled".format(disable_repo))
        #teardown        
        self.vm.delete()
        self.vm.user_data = save_userdata
        self.vm.create()
        time.sleep(30)
        self.params['remote_node'] = self.vm.floating_ip
        utils_lib.init_connection(self, timeout=self.timeout)

    def tearDown(self):
        if 'test_cloudinit_sshd_keypair' in self.id():
            cmd = 'cp -f ~/.ssh/authorized_keys.bak ~/.ssh/authorized_keys'
            utils_lib.run_cmd(self, cmd, msg='restore .ssh/authorized_keys')
            cmd= 'sudo systemctl restart  sshd'
            utils_lib.run_cmd(self, cmd, expect_ret=0, msg='restart sshd service')
        #utils_lib.finish_case(self)

if __name__ == '__main__':
    unittest.main()