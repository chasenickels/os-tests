from os_tests.common.constants import NOT_IMPLEMENTED
from os_tests.common.exceptions import DistroException
from os_tests.libs import utils_lib


class Distro(object):
    """Generic module for performing instance level tests."""

    def __init__(self):
        """Initialize distro class."""
        super(Distro, self).__init__()
        self.init_system = ""

    def _get_init_system(self):
        """Determine the init system of distribution."""
        out = utils_lib.run_cmd(self, "ps -p 1 -o comm=")
        init_system = out.strip()
        return init_system

    def _set_init_system(self):
        """Set the init system variable if not set."""
        if not self.init_system:
            self.init_system = self._get_init_system()

    def get_install_cmd(self):
        """Return install package command for distribution."""
        raise NotImplementedError(NOT_IMPLEMENTED)

    def get_installed_pkg_cmd(self):
        """Return command to list if package is installed."""
        raise NotImplementedError(NOT_IMPLEMENTED)

    def get_reboot_cmd(self):
        """Return reboot command for given distribution."""
        return "shutdown -r now"

    def get_refresh_repo_cmd(self):
        """Return refresh repo command for distribution."""
        raise NotImplementedError(NOT_IMPLEMENTED)

    def get_stop_ssh_service_cmd(self):
        """Return command to stop SSH service on given distribution."""
        raise NotImplementedError(NOT_IMPLEMENTED)

    def get_sudo_exec_wrapper(self):
        """Return sudo command to wrap one or more commands."""
        return "sudo sh -c"

    def get_update_cmd(self):
        """Return command to update instance."""
        raise NotImplementedError(NOT_IMPLEMENTED)

    def get_vm_info(self):
        """Return vm info."""
        out = ""
        self._set_init_system()

        if self.init_system == "systemd":
            try:
                out += "systemd-analyze:\n\n"
                out += utils_lib.run_cmd(self, "systemd-analyze")

                out += "systemd-analyze blame:\n\n"
                out += utils_lib.run_cmd(self, "systemd-analyze blame")

                out += "journalctl -b:\n\n"
                out += utils_lib.run_cmd(self, "sudo journalctl -b")
            except Exception as error:
                out = "Failed to collect VM info: {0}.".format(error)

        return out

    def install_package(self, package):
        """Install package on instance."""
        install_cmd = "sudo {install} {package}".format(
            install=self.get_install_cmd(), package=package
        )
        return install_cmd

    def list_package(self, package):
        """Get installed package on instance."""
        get_pkg = "sudo {get_package} {package}".format(
            get_package=self.get_installed_pkg_cmd(), package=package
        )
        return get_pkg

    # def reboot(self):
    #     """Execute reboot command on instance."""
    #     self._set_init_system()

    #     reboot_cmd = \
    #         "{sudo} '(sleep 1 && {stop_ssh} && {reboot} &)' && exit".format(
    #             sudo=self.get_sudo_exec_wrapper(),
    #             stop_ssh=self.get_stop_ssh_service_cmd(),
    #             reboot=self.get_reboot_cmd()
    #         )

    #     try:
    #         transport = client.get_transport()
    #         channel = transport.open_session()
    #         channel.exec_command(reboot_cmd)
    #         time.sleep(2)  # Required for delay in reboot
    #         transport.close()
    #     except Exception as error:
    #         raise DistroException(
    #             'An error occurred rebooting instance: %s' % error
    #         )
    #     ipa_utils.clear_cache()

    def update(self):
        """Execute update command on instance."""
        update_cmd = "{sudo} '{refresh};{update}'".format(
            sudo=self.get_sudo_exec_wrapper(),
            refresh=self.get_refresh_repo_cmd(),
            update=self.get_update_cmd(),
        )

        out = ""
        try:
            out = utils_lib.run_cmd(self, update_cmd)
        except Exception as error:
            raise DistroException("An error occurred updating instance: %s" % error)
        return out

    def repo_refresh(self):
        """Execute repo refresh command on instance."""
        update_cmd = "{sudo} '{refresh}'".format(
            sudo=self.get_sudo_exec_wrapper(), refresh=self.get_refresh_repo_cmd()
        )

        out = ""
        try:
            out = utils_lib.run_cmd(self, update_cmd)
        except Exception as error:
            raise DistroException("An error occurred refreshing repos on instance: %s" % error)
        return out
