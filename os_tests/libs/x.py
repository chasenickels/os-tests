import re
import subprocess


def run_cmd(cmd="", timeout=120):
    status = None
    output = None
    ret = subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        encoding="utf-8",
    )
    status = ret.returncode
    if ret.stdout is not None:
        output = ret.stdout
    return output if status == 0 else None


def replace_string(bad_string: str, good_string: str, target_file: str, stig_id: str):
    with open(target_file, "r") as f:
        for line in f:
            bad_match = re.match(bad_string, line)
            good_match = re.match(good_string, line)
            if good_match:
                return f"{good_string} found in {target_file}, per {stig_id}."
            if bad_match:
                bad_match = bad_match.string.strip("\n")
                cmd = f"sed -ri 's/{bad_match}/{good_string}/g' {target_file}"
                new_cmd = f'sudo bash -c "{cmd}"'
                run_cmd(
                    new_cmd,
                )
                return f"{bad_match} replaced with {good_string}, per {stig_id}."
    run_cmd(f"echo {good_string} >> {target_file}")


# replace_string(r".*poop.*", r"hello", "/tmp/x.txt" , "V-11234")
