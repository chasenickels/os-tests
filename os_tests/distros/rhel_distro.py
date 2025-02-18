from os_tests.common.exceptions import RHELDistroException
from os_tests.distros.distro import Distro


class RHEL(Distro):
    """RHEL distro class."""

    def get_install_cmd(self):
        """Return install package command for RHEL."""
        return "sudo dnf install -y"

    def get_installed_pkg_cmd(self, pkg_name=None):
        """Return command to list if package is installed for RHEL."""
        return f"rpm -q {pkg_name}"

    def get_stop_ssh_service_cmd(self):
        """
        Return command to stop SSH service for RHEL.

        SSH stop command determined by init system.
        """
        if self.init_system == "systemd":
            return "sudo systemctl stop sshd.service"
        elif self.init_system == "init":
            return "rcsshd stop"
        else:
            raise RHELDistroException(
                "The init system for RHEL distribution cannot be determined."
            )

    def get_update_cmd(self):
        """Return command to update RHEL instance."""
        return "sudo dnf update -y"

    def install_cmd(self, pkg_name=None):
        """Return install package command for RHEL."""
        return f"sudo dnf install -y {pkg_name}"

    def reinstall_cmd(self, pkg_name=None):
        """Return reinstall package command for RHEL."""
        return f"sudo dnf reinstall -y {pkg_name}"

    def install_nodeps(self, pkg_url=None):
        """Return install package command with no dependencies for RHEL."""
        return f"sudo rpm -ivh {pkg_url} --nodeps"

    def is_pkg_installed(self, pkg_name=None):
        """Return command to list if package is installed for RHEL."""
        return f"rpm -q {pkg_name}"
