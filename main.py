import os
import atexit
import typer
import pathlib
import tempfile
import subprocess as sp
import shutil

app = typer.Typer()

CONFIG = {
    "DEPLOY_COMPRESSION": "none",
    "ENABLE_SSH": "1",
    "PUBKEY_ONLY_SSH": "1",
    "STAGE_LIST": "stage0 stage1 stage2",
}


def create_ssh_key(hostname: str):
    sp.check_call(
        [
            "op",
            "item",
            "create",
            "--category=ssh-key",
            "--ssh-generate-key=ed25519",
            "--title",
            f"{hostname}.local",
        ]
    )


def get_public_key(hostname: str):
    return sp.check_output(
        [
            "op",
            "read",
            f"op://private/{hostname}.local/public key",
        ],
        text=True,
    )


@app.command()
def build(hostname: str, user: str = "znd4"):
    not_installed = {app for app in ["op"] if not shutil.which(app)}
    if not_installed:
        typer.echo(f"Please install the following CLI dependencies: {not_installed}")
        raise typer.Exit(code=1)

    CONFIG["HOSTNAME"] = hostname
    CONFIG["IMG_NAME"] = f"rasbpian-{hostname}"
    CONFIG["FIRST_USER_NAME"] = user

    try:
        public_key = get_public_key(hostname)
    except sp.CalledProcessError:
        create_ssh_key(hostname)
        public_key = get_public_key(hostname)

    public_key = sp.check_output(
        [
            "op",
            "read",
            f"op://private/{hostname}.local/public key",
        ],
        text=True,
    )
    CONFIG["PUBKEY_SSH_FIRST_USER"] = public_key

    sp.check_call(["docker-compose", "up", "-d"])
    atexit.register(lambda: sp.check_call(["docker-compose", "down"]))
    CONFIG["APT_PROXY"] = "http://localhost:3142"

    cfg = pathlib.Path("config")

    cfg.unlink(missing_ok=True)
    cfg.write_text("\n".join(f"{k}={v!r}" for k, v in CONFIG.items()))
    sp.check_call(
        [
            "sudo",
            "bash",
            "build.sh",
            # "build-docker.sh",
            "-c",
            str(cfg),
        ]
    )


if __name__ == "__main__":
    app()
