class MandoException(Exception):
    """Generic exception for the img_proof package."""


class DistroException(MandoException):
    """Generic Exception for distro modules."""


class SLESDistroException(DistroException):
    """Generic Exception for distro modules."""


class UbuntuDistroException(DistroException):
    """Generic Exception for Ubuntu distro modules."""


class RHELDistroException(DistroException):
    """Generic Exception for RHEL distro modules."""
