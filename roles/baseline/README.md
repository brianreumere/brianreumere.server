# baseline

## Overview

Does baseline configuration of a Debian/Ubuntu, RHEL, or OpenBSD server:

- Sets system hostname
- Sets timezone
- Installs package upgrades (optional)
- Installs QEMU guest agent (optional)
- Installs some basic useful packages
- Enables a firewall
- Adds a non-root user, adds authorized SSH keys, and allows the user to use `sudo` or `doas`
- Disallows root SSH login and password-based SSH login
- Enables automatic package upgrades (optionally including non-security upgrades)

## Variables

### Optional

- `hostname`: System hostname (fully-qualified), defaults to `inventory_hostname`
- `upgrade_packages`: Whether the role should run a package upgrade, defaults to `false` (can be useful to set to `true` on the initial application of the role)
- `install_qemu_guest_agent`: Whether the QEMU guest agent should be installed, defaults to `false` (has no affect on OpenBSD)
- `timezone`: Timezone, defaults to `UTC`
- `enable_firewall`: Whether to enable a firewall, defaults to `true`
- `allowed_ports`: Dict of ports and protocols to allow, defaults to:
    ```yaml
    - port: 22
      proto: tcp
    ```
- `debian_baseline_packages`: List of packages to install on Debian/Ubuntu, defaults to:
    ```yaml
    - unattended-upgrades
    - tmux
    - vim
    - net-tools
    ```
- `rhel_baseline_packages`: List of packages to install on RHEL, defaults to:
    ```yaml
    - dnf-automatic
    - tmux
    - vim
    - net-tools
    ```
- `openbsd_baseline_packages`: List of packages to install on OpenBSD, `[]` by default because OpenBSD includes useful packages in the base system
- `install_nonsecurity_upgrades`: Whether to enable automatic installation of non-security package/OS upgrades, defaults to `false` (has no affect on OpenBSD)

#### RHEL-only

Some variables that can be used to activate a RHEL subscription:

- `redhat_subscription`: Whether to register a RHEL subscription, defaults to `false`
- `redhat_activation_key`: Activation key, required if activating a subscription
- `redhat_org_id`: RedHat organization ID, required if activating a subscription
- `redhat_repos`: Additional repos to enable (for example, `codeready-builder-for-rhel-9-x86_64-rpms`), defaults to `[]`
- `rhel_syspurpose_usage`: System usage, defaults to `Development/Test`
- `rhel_syspurpose_role`: System role, defaults to `RHEL Server`
- `rhel_syspurpose_service_level_agreement`: System SLA, defaults to `Self-Support`

Some of these (probably activation key and org ID) should be set in an [Ansible vault file](https://docs.ansible.com/ansible/latest/vault_guide/vault_encrypting_content.html#encrypting-files-with-ansible-vault) or stored in another secrets manager. For example:

```sh
ansible-vault create rhel_secrets.yml
```

## Example

```yaml
---
- name: Apply baseline
  ansible.builtin.include_role:
    name: brianreumere.server.baseline
  vars:
    install_qemu_guest_agent: true
    allowed_ports:
      - port: 22
        proto: tcp
      - port: 80
        proto: tcp
      - port: 443
        proto: tcp
```
