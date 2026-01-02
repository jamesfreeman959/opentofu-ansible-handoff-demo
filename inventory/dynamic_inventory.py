#!/usr/bin/env python3
"""
Dynamic Ansible inventory script that reads OpenTofu state.

This script reads the terraform.tfstate file and generates an Ansible inventory
with the EC2 instance information from OpenTofu outputs.
"""

import json
import sys
import subprocess


def get_tofu_outputs():
    """
    Get outputs from OpenTofu state.

    Returns:
        dict: Dictionary of OpenTofu outputs
    """
    try:
        result = subprocess.run(
            ['tofu', 'output', '-json'],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running tofu output: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing tofu output: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'tofu' command not found. Please ensure OpenTofu is installed.", file=sys.stderr)
        sys.exit(1)


def build_inventory():
    """
    Build Ansible inventory from OpenTofu outputs.

    Returns:
        dict: Ansible inventory in JSON format
    """
    outputs = get_tofu_outputs()

    # Extract values from outputs
    public_ip = outputs.get('instance_public_ip', {}).get('value')
    ssh_user = outputs.get('ssh_user', {}).get('value', 'ec2-user')

    if not public_ip:
        print("Error: No public IP found in OpenTofu outputs", file=sys.stderr)
        sys.exit(1)

    # Build inventory structure
    inventory = {
        'web_servers': {
            'hosts': [public_ip],
            'vars': {
                'ansible_user': ssh_user,
                'ansible_ssh_private_key_file': './demo-key'
            }
        },
        '_meta': {
            'hostvars': {
                public_ip: {
                    'ansible_host': public_ip,
                    'ansible_user': ssh_user
                }
            }
        }
    }

    return inventory


def main():
    """
    Main entry point for the inventory script.
    """
    # Ansible will call this script with --list or --host <hostname>
    if len(sys.argv) == 2 and sys.argv[1] == '--list':
        inventory = build_inventory()
        print(json.dumps(inventory, indent=2))
    elif len(sys.argv) == 3 and sys.argv[1] == '--host':
        # Return empty dict for --host as we provide hostvars in _meta
        print(json.dumps({}))
    else:
        print("Usage: dynamic_inventory.py --list or --host <hostname>", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
