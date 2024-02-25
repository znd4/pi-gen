import subprocess as sp
import json
import shlex
import argparse


def main():
    parser = argparse.ArgumentParser(description="Build and install ssh")
    parser.add_argument("--hostname", help="The hostname of the server", required=True)
    args = parser.parse_args()
    hostname = args.hostname
    public_key = ensure_public_key(hostname=hostname)

    sp.check_call(
        ["./build-docker.sh"],
        env={
            "ENABLE_SSH": "1",
            "PUBKEY_ONLY_SSH": "1",
            "PUBKEY_SSH_FIRST_USER": public_key,
            "TARGET_HOSTNAME": hostname,
            "IMG_NAME": f"rasbpian-ssh-{hostname}",
        },
    )


def ensure_public_key(hostname: str):
    """
    Make sure that an ssh server entry exists for the given hostname in 1password
    """
    code, output = sp.getstatusoutput(
        shlex.join(
            [
                "op",
                "get",
                "item",
                f"{hostname}.local",
                "--fields",
                "public_key",
            ]
        )
    )
    if code == 0:
        return output
    fields = json.loads(
        sp.check_output(
            [
                "op",
                "item",
                "create",
                "--category",
                "ssh",
                "--title",
                f"{hostname}.local",
                "--format=json",
            ]
        )
    )["fields"]
    return [f["value"] for f in fields if f["id"] == "public_key"][0]


main()
