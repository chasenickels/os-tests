import logging
import os
import time
from contextlib import contextmanager
from functools import wraps

from .harness import Harness

LOGLEVEL = os.environ.get("SSM_LOG_LEVEL", "INFO").upper()
logging.basicConfig(format="%(levelname)-8s %(message)s", level=LOGLEVEL)
LOGGER = logging.getLogger(__file__.split(os.path.sep)[-1].rsplit(".", 1)[0])


@contextmanager
def EC2InstanceManager(
    session,
    create_instances_arguments,
    initial_state="running",
    ssm_managed=False,
    client_config=None,
):  # noqa: N802
    """
    The EC2InstanceManager is set up with some standard EC2 inputs and,
    when applied, creates an EC2 instance. When the Harness is torn
    down, the EC2 instance is terminated. The boto3 resource for the
    EC2 instance is returned.
    """

    available_states = ["running", "stopped"]
    instance_ids = None

    if "MinCount" not in create_instances_arguments:
        create_instances_arguments["MinCount"] = 1

    if "MaxCount" not in create_instances_arguments:
        create_instances_arguments["MaxCount"] = 1

    if initial_state not in available_states:
        raise ValueError(
            f"Invalid EC2 state. Provided {initial_state}, available states: {available_states} "
        )

    if ssm_managed and create_instances_arguments.get("IamInstanceProfile") is None:
        raise ValueError(
            "You must specify IamInstanceProfile in order to create an SSM managed EC2 instance"
        )

    if ssm_managed and initial_state != "running":
        raise ValueError(
            "You must specify a running initial state in order to create an SSM managed EC2 instance"
        )

    try:
        LOGGER.info("Creating EC2 instance")

        ec2_resource = session.resource("ec2")
        ec2_client = session.client("ec2", config=client_config)

        result = ec2_client.run_instances(**create_instances_arguments)
        instances = [
            ec2_resource.Instance(instance["InstanceId"])
            for instance in result["Instances"]
        ]

        instance_ids = [instance["InstanceId"] for instance in result["Instances"]]

        LOGGER.debug(
            f"Waiting for EC2 instance(s) {','.join(instance_ids)} to be {initial_state}"
        )
        if initial_state == "running":
            for instance in instances:
                instance.wait_until_running()

            LOGGER.debug(
                f"Done waiting for {','.join(instance_ids)} to be {initial_state}"
            )

            LOGGER.debug(
                f"Waiting for {','.join(instance_ids)} to pass the health checks"
            )
            attempts = 0
            while (
                any(
                    (
                        (d["InstanceStatus"]["Status"] != "ok")
                        or (d["SystemStatus"]["Status"] != "ok")
                    )
                    for d in session.client("ec2").describe_instance_status(
                        InstanceIds=instance_ids, IncludeAllInstances=True
                    )["InstanceStatuses"]
                )
                and attempts < 40
            ):
                LOGGER.debug(
                    f"Attempt {attempts+1}: Instance(s) still initializing; waiting {15} seconds and checking again"
                )
                time.sleep(15)
                attempts += 1

            LOGGER.debug(
                f"Done waiting for {','.join(instance_ids)} to pass the health checks"
            )

        if initial_state == "stopped":
            for instance in instances:
                instance.wait_until_stopped()

            LOGGER.debug(
                f"Done waiting for {','.join(instance_ids)} to be {initial_state}"
            )

        if ssm_managed:
            LOGGER.info(
                f"Waiting for EC2 instance(s) {','.join(instance_ids)} to be managed"
            )
            attempts = 0
            while (
                any(
                    d["PingStatus"] != "Online"
                    for d in session.client("ssm").describe_instance_information(
                        Filters=[{"Key": "InstanceIds", "Values": instance_ids}]
                    )["InstanceInformationList"]
                )
                and attempts < 40
            ):
                LOGGER.debug(
                    f"Instance(s) still not managed; waiting {15} seconds and checking again"
                )
                time.sleep(15)
                attempts += 1

            LOGGER.debug(f"Done waiting for {','.join(instance_ids)} to be managed")

        yield {"ec2": {"instances": instances, "instance_ids": instance_ids}}

    finally:
        if instance_ids:
            LOGGER.info(f"Terminating EC2 instance(s) {','.join(instance_ids)}")
            for instance in instances:
                instance.terminate()
            LOGGER.debug("Waiting for EC2 termination to complete")
            for instance in instances:
                instance.wait_until_terminated()


def instance(create_instances_arguments, initial_state="running", ssm_managed=False):
    """
    Sets the context class attributes via EC2:
    obj.context = Dictionary of context resources (EC2 instance resources)
    """

    def set_ec2_harness(func):
        @wraps(func)
        def wrapper(obj, *args, **kwargs):
            new_context = obj.context_manager.enter_context(
                Harness(
                    context_manager=EC2InstanceManager(
                        session=obj.session,
                        create_instances_arguments=create_instances_arguments,
                        initial_state=initial_state,
                        ssm_managed=ssm_managed,
                    ),
                    context=obj.context,
                )
            )

            obj.context = new_context

            try:
                func(obj, *args, **kwargs)
            finally:
                obj.context_manager.pop_all().close()

        return wrapper

    return set_ec2_harness
