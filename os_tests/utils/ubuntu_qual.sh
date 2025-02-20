#!/bin/bash
function main() {
# Determining the newly attached device and partition based on device type.
DEVICE=$(lsblk -o PATH,SIZE | grep 100G | awk '{print $1}')
[[ $DEVICE == *"nvme"* ]] && PART=p1 || PART=1

DEBIAN_FRONTEND=noninteractive apt update && DEBIAN_FRONTEND=noninteractive apt dist-upgrade -y && DEBIAN_FRONTEND=noninteractive apt install iperf3 fio -y | tee /home/ubuntu/logfile.txt
if [[ $(lsb_release -c | awk '{print $2}') == "bionic" ]]; then DEBIAN_FRONTEND=noninteractive apt install ec2-instance-connect -y;fi
echo "*********** SSH KEY BEGIN **********" | tee -a /home/ubuntu/logfile.txt
ssh-import-id lp:cnewcomer | tee -a /home/ubuntu/logfile.txt
echo "*********** SSH KEY END **********" | tee -a /home/ubuntu/logfile.txt

cat > /home/ubuntu/stuff.sh <<EOF1
#!/bin/bash
printf "CPU/RAM OUTPUT\n###### BEGIN ######\n"
printf "CPUS = "
nproc
printf "RAM = "
free | grep Mem | awk '{print \$2}'
printf "\n###### END ######\n"
EOF1
chmod 755 /home/ubuntu/stuff.sh
cat > /home/ubuntu/sos.sh <<EOF2
#!/bin/bash
sudo sos report -a --all-logs --batch
EOF2
chmod 755 /home/ubuntu/sos.sh

cat > /home/ubuntu/disk.layout <<EOF3
label: dos
label-id: 0x0a7d0f7c
device: $DEVICE
unit: sectors
$DEVICE$PART : start=        2048, size=   209713152, type=83
EOF3

cat > /home/ubuntu/fio.sh <<EOF4
#!/bin/bash

if [[ \$(grep data /proc/mounts) ]]; then
sudo fio --name=read_iops_test \
  --filename=$DEVICE --filesize=50G \
  --time_based --ramp_time=2s --runtime=1m \
  --ioengine=libaio --direct=1 --verify=0 --randrepeat=0 \
  --bs=16K --iodepth=256 --rw=randread
else
    echo "---------------- /data NOT MOUNTED ------------------------------"
fi
EOF4
chmod 755 /home/ubuntu/fio.sh

sfdisk $DEVICE < /home/ubuntu/disk.layout
sleep 2
mkfs.xfs -b size=4096 $DEVICE$PART
mkdir /data
mount -t xfs $DEVICE$PART /data
# Needs to stay commented out unless the volume is staying attached to the instance, it will cause emergency mode on reboot
# because vol cannot be found.
# echo "$DEVICE$PART    /data    xfs    defaults    0    1" | sudo tee -a /etc/fstab

echo "******** CPU/MEM RESULTS ********" | tee -a /home/ubuntu/logfile.txt
/home/ubuntu/stuff.sh | tee -a /home/ubuntu/logfile.txt
sleep 20

# Removing CTS information from cloud-init logs being sent to Canonical
mv /var/log/cloud-init-output.log /var/log/cloud-init-output.log.old
awk '/=========================== CTS CLOUD INIT SCRIPT ===========================/ {exit} {print}' /var/log/cloud-init-output.log.old | tee -a /var/log/cloud-init-output.log
grep -Ei "cloud-init.*finished.*" /var/log/cloud-init-output.log.old | tail -n 1 >> /var/log/cloud-init-output.log
rm -f /var/log/cloud-init-output.log.old

echo "******** SSM RESULTS ********" | tee -a /home/ubuntu/logfile.txt
(snap list | grep -q  amazon-ssm-agent && \               # omitting any arn/instance id information from logs :)
ssm-cli get-diagnostics | jq -c '.DiagnosticsOutput[]' | sed -e 's/i-.*\s/<omitted> /g' -e  's/arn.*\s/<omitted> /g' | jq -c | tee -a /home/ubuntu/logfile.txt) ||
echo "amazon-ssm-agent is not currently installed on this system." | tee -a /home/ubuntu/logfile.txt
MESSAGE="SSM send-command execution was successful."
"$AWS_BIN_PATH" ssm send-command \
--instance-ids $CURRENT_INSTANCE_ID \
--region $REGION \
--document-name "AWS-RunShellScript" \
--parameters commands="echo $MESSAGE >> /home/ubuntu/ssm_result.txt" \
--output text
(grep -q "$MESSAGE" /home/ubuntu/ssm_result.txt && echo "$MESSAGE" | tee -a /home/ubuntu/logfile.txt) ||
echo "SSM send-command execution failed." | tee -a /home/ubuntu/logfile.txt
echo "******** EC2 Instance Connect RESULTS ********" | tee -a /home/ubuntu/logfile.txt
# Setting inactive timeout really low because there is no good way to ssh non-interactively using ec2-instance-connect.
# This forces ssh connection to timeout while still exiting successfully.
echo "export TMOUT=10" >> /home/ubuntu/.bashrc
"$AWS_BIN_PATH" ec2-instance-connect ssh --instance-id $CURRENT_INSTANCE_ID --os-user ubuntu
([ $? == 0 ] && echo "EC2 Instance Connect was able to successfully connect to instance." | tee -a /home/ubuntu/logfile.txt) ||
echo "EC2 Instance Connect was failed connect to instance." | tee -a /home/ubuntu/logfile.txt
# Resetting timeout
echo "export TMOUT=300" >> /home/ubuntu/.bashrc
echo "******** FIO RESULTS ********" | tee -a /home/ubuntu/logfile.txt
/home/ubuntu/fio.sh | grep IOPS | tee -a /home/ubuntu/logfile.txt
echo "******** LSBLK RESULTS ********" | tee -a /home/ubuntu/logfile.txt
lsblk | tee -a /home/ubuntu/logfile.txt
echo "******** IRQBALANCE RESULTS ********" | tee -a /home/ubuntu/logfile.txt
grep -i irqbalance /var/log/syslog | tee -a /home/ubuntu/logfile.txt
echo "******** NVIDIA RESULTS ********" | tee -a /home/ubuntu/logfile.txt
lspci | grep NVIDIA | tee -a /home/ubuntu/logfile.txt
echo "******** SOSREPORT RESULTS ********" | tee -a /home/ubuntu/logfile.txt
/home/ubuntu/sos.sh | tee -a /home/ubuntu/logfile.txt
cp /tmp/sosreport*.tar.xz /home/ubuntu/sosreport.tar.xz
chown ubuntu:ubuntu /home/ubuntu/sosreport.tar.xz
install_hotsos
echo "******** HOTSOSREPORT RESULTS ********" | tee -a /home/ubuntu/logfile.txt
sudo hotsos --sosreport /home/ubuntu/sosreport.tar.xz | tee -a /var/log/cloud-init-output.log
dmesg | tee -a /home/ubuntu/dmesg.txt
cp /var/log/kern.log /var/log/syslog /var/log/cloud-init-output.log /home/ubuntu
}

. ./assets/helper-funcs.sh
install_requirements
install_aws_cli
VOLUME_TYPE=$(aws ec2 describe-instances --instance-id $CURRENT_INSTANCE_ID --query 'Reservations[*].Instances[*].RootDeviceType' --output text)

if [ $VOLUME_TYPE != "instance-store" ]; then
  handle_attach
  main
  handle_delete
else
  main
  echo "INSTANCE ROOT VOLUME TYPE DOES NOT SUPPORT ADDITION OF EBS VOLUMES, SKIPPING FIO." | tee -a /home/ubuntu/logfile.txt
fi
