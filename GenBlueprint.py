import json
import os
import argparse

def load_json(file_path):
    """
    Load the JSON file containing server configuration.
    
    Args:
        file_path (str): Path to the JSON file.
    
    Returns:
        dict: Loaded JSON data.
    """
    with open(file_path, 'r') as json_file:
        return json.load(json_file)

def create_playbook_directory():
    """Create a directory for playbooks if it doesn't exist."""
    if not os.path.exists("playbooks"):
        os.makedirs("playbooks")

def generate_packages_playbook(data):
    """
    Generate a playbook to install packages.
    
    Args:
        data (dict): Server configuration data.
    """
    packages = [pkg['name'] for pkg in data.get('installed_packages', [])]
    playbook_content = f"""
---
- hosts: all
  become: yes
  tasks:
    - name: Install required packages
      apt:
        name:
          - {'\n          - '.join(packages)}
        state: present
        update_cache: yes
    """
    with open("playbooks/packages.yml", "w") as playbook_file:
        playbook_file.write(playbook_content)

def generate_services_playbook(data):
    """
    Generate a playbook to start required services.
    
    Args:
        data (dict): Server configuration data.
    """
    services = ["cron"]  # Add other services if needed
    playbook_content = f"""
---
- hosts: all
  become: yes
  tasks:
    - name: Ensure services are running
      service:
        name: "{{{{ item }}}}"
        state: started
      loop:
        - {'\n        - '.join(services)}
    """
    with open("playbooks/services.yml", "w") as playbook_file:
        playbook_file.write(playbook_content)

def generate_network_playbook(data):
    """
    Generate a playbook to configure network.
    
    Args:
        data (dict): Server configuration data.
    """
    network_info = data.get('network', {})
    ip_addr = network_info.get('ip_addr', 'N/A')
    playbook_content = f"""
---
- hosts: all
  become: yes
  tasks:
    - name: Display network configuration (for manual intervention)
      debug:
        msg: "Current network configuration: {ip_addr}"
    """
    with open("playbooks/network.yml", "w") as playbook_file:
        playbook_file.write(playbook_content)

def generate_main_playbook():
    """Generate the main playbook to include all others."""
    main_playbook_content = """
---
- import_playbook: packages.yml
- import_playbook: services.yml
- import_playbook: network.yml
- import_playbook: ssh.yml
    """
    with open("playbooks/site.yml", "w") as playbook_file:
        playbook_file.write(main_playbook_content)

def update_inventory(hostname, public_ip):
    """
    Update the Ansible inventory file.
    
    Args:
        hostname (str): The hostname of the server.
        public_ip (str): The public IP address of the server.
    """
    inventory_file = "playbooks/inventory"
    inventory_entry = f"{hostname} ansible_host={public_ip} ansible_user=root ansible_ssh_private_key_file=/path/to/your/private/key"

    if os.path.exists(inventory_file):
        with open(inventory_file, 'r') as f:
            inventory_content = f.read()
        if hostname not in inventory_content:
            with open(inventory_file, 'a') as f:
                f.write(f"\n{inventory_entry}")
    else:
        with open(inventory_file, 'w') as f:
            f.write(inventory_entry)

def generate_ssh_playbook(data):
    """
    Generate a playbook to configure SSH.
    
    Args:
        data (dict): Server configuration data.
    """
    ssh_config = data.get('ssh_config', '')
    playbook_content = f"""
---
- hosts: all
  become: yes
  tasks:
    - name: Configure SSH
      copy:
        content: |
{ssh_config}
        dest: /etc/ssh/sshd_config
        owner: root
        group: root
        mode: '0644'
    
    - name: Restart SSH service
      service:
        name: sshd
        state: restarted
    """
    with open("playbooks/ssh.yml", "w") as playbook_file:
        playbook_file.write(playbook_content)

def main():
    parser = argparse.ArgumentParser(description="Generate Ansible playbooks from JSON configuration.")
    parser.add_argument("json_file", help="Path to the JSON configuration file")
    args = parser.parse_args()

    data = load_json(args.json_file)
    
    create_playbook_directory()
    
    generate_packages_playbook(data)
    generate_services_playbook(data)
    generate_network_playbook(data)
    generate_ssh_playbook(data)
    
    generate_main_playbook()

    hostname = data.get('hostname', 'unknown')
    public_ip = data.get('public_ip', 'unknown')
    update_inventory(hostname, public_ip)

    print("Playbooks have been generated in the 'playbooks' directory.")
    print("Inventory file has been updated.")
    print("\nTo test these playbooks, run the following Ansible command:")
    print(f"ansible-playbook -i playbooks/inventory playbooks/site.yml")

if __name__ == "__main__":
    main()
