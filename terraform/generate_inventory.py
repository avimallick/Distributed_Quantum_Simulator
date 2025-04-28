#!/usr/bin/env python3

import json
import subprocess
import argparse

def run(command):
    return subprocess.run(command, capture_output=True, encoding='UTF-8')

def generate_inventory():
    command = "terraform output --json dynamic_inventory".split()
    ip_data = json.loads(run(command).stdout)

    host_vars = {}
    management = ip_data["management"]
    workers = ip_data["workers"]
    storage = ip_data["storage"]

    for ip in management:
        host_vars[ip] = { "role": "management" }
    for ip in workers:
        host_vars[ip] = { "role": "worker" }
    if storage:
        host_vars[storage] = { "role": "storage" }

    _meta = {"hostvars": host_vars}
    _all = {"children": ["management", "workers", "storage"]}

    inventory = {
        "_meta": _meta,
        "all": _all,
        "management": {"hosts": management},
        "workers": {"hosts": workers},
        "storage": {"hosts": [storage]} if storage else {},
    }

    return json.dumps(inventory, indent=4)

if __name__ == "__main__":

    ap = argparse.ArgumentParser(
        description="Generate an Ansible inventory from Terraform outputs.",
        prog=__file__
    )

    mo = ap.add_mutually_exclusive_group()
    mo.add_argument("--list", action="store_true", help="Show JSON of all managed hosts")
    mo.add_argument("--host", action="store", help="Display vars related to the host")
    ap.add_argument("--file", action="store", help="Save inventory to a file")

    args = ap.parse_args()

    jd = generate_inventory()

    if args.host:
        host = args.host
        inventory = json.loads(jd)
        if host in inventory["_meta"]["hostvars"]:
            print(json.dumps(inventory["_meta"]["hostvars"][host]))
        else:
            print(json.dumps({}))
    elif args.list:
        if args.file:
            with open(args.file, "w") as f:
                f.write(jd)
        else:
            print(jd)
    else:
        raise ValueError("Expecting either --host $HOSTNAME or --list")
