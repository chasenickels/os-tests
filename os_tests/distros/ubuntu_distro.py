from os_tests.common.exceptions import UbuntuDistroException
from os_tests.distros.distro import Distro


class Ubuntu(Distro):
    """Ubuntu distro class."""

    def get_install_cmd(self):
        """Return install package command for Ubuntu."""
        return "apt-get install -y"

    def get_installed_pkg_cmd(self):
        """Return command to list if package is installed for Ubuntu."""
        return "dpkg -l"

    def get_stop_ssh_service_cmd(self):
        """
        Return command to stop SSH service for Ubuntu.

        SSH stop command determined by init system.
        """
        if self.init_system == "systemd":
            return "systemctl stop sshd.service"
        elif self.init_system == "init":
            return "rcsshd stop"
        else:
            raise UbuntuDistroException(
                "The init system for Ubuntu distribution cannot be determined."
            )

    def get_update_cmd(self):
        """Return command to update Ubuntu instance."""
        return "apt-get update -y"
