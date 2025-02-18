from os_tests.common.exceptions import SLESDistroException
from os_tests.distros.distro import Distro


class SLES(Distro):
    """SLES distro class."""

    def get_install_cmd(self):
        """Return install package command for SLES."""
        return "zypper --non-interactive install -y"

    def get_installed_pkg_cmd(self):
        """Return command to list if package is installed for SLES."""
        return "zypper search -i"

    def get_refresh_repo_cmd(self):
        """Return refresh repo command for SLES."""
        return "zypper --non-interactive refresh"

    def get_stop_ssh_service_cmd(self):
        """
        Return command to stop SSH service for SLES.

        SSH stop command determined by init system.
        """
        if self.init_system == "systemd":
            return "systemctl stop sshd.service"
        elif self.init_system == "init":
            return "rcsshd stop"
        else:
            raise SLESDistroException("The init system for SUSE distribution cannot be determined.")

    def get_update_cmd(self):
        """Return command to update SLES instance."""
        return (
            "zypper --non-interactive update --auto-agree-with-licenses "
            "--force-resolution --replacefiles"
        )

    def is_pkg_installed(self, pkg_name=None):
        """Return command to list if package is installed for RHEL."""
        return f"rpm -q {pkg_name}"
