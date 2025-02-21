import string
import time

import boto3
import requests

"https://github.com/adamchainz/ec2-metadata/blob/main/src/ec2_metadata/__init__.py"


class VolumeManager(object):
    def __init__(self):
        self._session = requests.Session()
        self._token_updated_at = 0.0
        self.service_url = "http://169.254.169.254/latest/"
        self.metadata_url = f"{self.service_url}meta-data/"
        self.dynamic_url = f"{self.service_url}dynamic/"
        self.TOKEN_TTL_SECONDS = 21600
        self.TOKEN_HEADER = "X-aws-ec2-metadata-token"
        self.TOKEN_HEADER_TTL = "X-aws-ec2-metadata-token-ttl-seconds"
        self.ec2_client = boto3.client("ec2", region_name=self._return_region())

    def __enter__(self):
        if self._is_instance_store_back():
            return

        self.volume_id = self._create_volume("UbuntuInstanceQual")
        self._attach_volume(self.volume_id, self._return_availability_zone())

    def __exit__(self, exc_type, exc_value, traceback):
        if self._is_instance_store_back():
            return

        self._detach_and_delete_volume(self.volume_id)

    def _get_token(self):
        now = time.time()
        # Refresh up to 60 seconds before expiry
        if now - self._token_updated_at > (self.TOKEN_TTL_SECONDS - 60):
            token_response = self._session.put(
                f"{self.service_url}api/token",
                headers={self.TOKEN_HEADER_TTL: str(self.TOKEN_TTL_SECONDS)},
                timeout=5.0,
            )
            if token_response.status_code != 200:
                token_response.raise_for_status()
            token = token_response.text
            self._session.headers.update({self.TOKEN_HEADER: token})
            self._token_updated_at = now

    def _get_url(self, url: str, allow_404: bool = False) -> requests.Response:
        self._get_token()
        resp = self._session.get(url, timeout=1.0)
        if resp.status_code != 404 or not allow_404:
            resp.raise_for_status()
        return resp

    def _return_instance_id(self):
        return self._get_url(f"{self.metadata_url}instance-id").text

    def _return_availability_zone(self):
        return self._get_url(f"{self.metadata_url}placement/availability-zone").text

    def _return_region(self):
        result = self._get_url(f"{self.dynamic_url}instance-identity/document").json()

        return result["region"]

    def _create_volume(self, tag_name=None):
        tag_name = tag_name if tag_name else "VolumeManager"
        return self.ec2_client.create_volume(
            AvailabilityZone=self._return_availability_zone(),
            Encrypted=False,
            Size=30,
            VolumeType="gp3",
            TagSpecifications=[
                {
                    "ResourceType": "volume",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": f"{tag_name}-{self._return_instance_id()}",
                        }
                    ],
                }
            ],
        )["VolumeId"]

    def _detach_and_delete_volume(self, volume_id):
        self.ec2_client.get_waiter("volume_available").wait(VolumeIds=[volume_id])
        self.ec2_client.detach_volume(
            VolumeId=volume_id,
            Force=True,
        )
        self.ec2_client.delete_volume(VolumeId=volume_id)

    def _attach_volume(self, volume_id, instance_id):
        self.ec2_client.get_waiter("volume_available").wait(VolumeIds=[volume_id])
        self.ec2_client.attach_volume(
            Device=self._get_available_device_id(),
            InstanceId=instance_id,
            VolumeId=volume_id,
        )

    def _is_instance_store_back(self):
        device_type = self.ec2_client.describe_instances(
            InstanceIds=[self._return_instance_id()]
        )["Reservations"][0]["Instances"][0]["RootDeviceType"]

        return device_type == "instance-store"

    def _get_available_device_id(self):
        last_device_letter = [
            device["DeviceName"]
            for device in self.ec2_client.describe_instances(
                InstanceIds=[self._return_instance_id()]
            )["Reservations"][0]["Instances"][0]["BlockDeviceMappings"]
        ][-1][-2]

        all_letters = list(string.ascii_lowercase)
        for i in range(len(all_letters) - 1):
            if all_letters[i] == last_device_letter:
                return "/dev/sb" + all_letters[i + 1]
