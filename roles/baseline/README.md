# baseline

## Overview

Does baseline configuration of a Debian/Ubuntu, RHEL, or OpenBSD server:

- Sets system hostname
- Sets timezone
- Installs package upgrades (optional)
- Installs QEMU guest agent (optional, not available for OpenBSD)
- Installs some basic useful packages
- Enables a firewall
- Adds a non-root user, adds authorized SSH keys, and allows the user to use `sudo` or `doas`
- Disables root SSH logins and password-based SSH logins
- Enables automatic package upgrades (for all packages and the base system on OpenBSD, and optionally including non-security apt/dnf upgrades on Linux variants)

## Variables

### Required

- `baseline_nonroot_user`: The username for the non-root user
- `baseline_ssh_authorized_keys`: A list of public SSH keys to authorize for the non-root user

### Optional

- `baseline_hostname`: System hostname (fully-qualified), defaults to `inventory_hostname`
- `baseline_upgrade_packages`: Whether the role should run a package upgrade, defaults to `false` (can be useful to set to `true` on the initial application of the role)
- `baseline_install_qemu_guest_agent`: Whether the QEMU guest agent should be installed, defaults to `false` (has no affect on OpenBSD)
- `baseline_timezone`: Timezone, defaults to `UTC`
- `baseline_enable_firewall`: Whether to enable a firewall, defaults to `true`
- `baseline_allowed_ports`: Dict of ports and protocols to allow, defaults to:
```yaml
- port: 22
  proto: tcp
```
- `baseline_debian_packages`: List of packages to install on Debian/Ubuntu, defaults to:
```yaml
- unattended-upgrades
- tmux
- vim
- net-tools
```
- `baseline_rhel_packages`: List of packages to install on RHEL, defaults to:
```yaml
- dnf-automatic
- tmux
- vim
- net-tools
```
- `baseline_openbsd_packages`: List of packages to install on OpenBSD, `[]` by default because OpenBSD includes useful packages in the base system
- `baseline_install_nonsecurity_upgrades`: Whether to enable automatic installation of non-security package/OS upgrades, defaults to `false` (has no affect on OpenBSD)

#### RHEL-only

Some variables that can be used to activate a RHEL subscription:

- `baseline_redhat_subscription`: Whether to register a RHEL subscription, defaults to `false`
- `baseline_redhat_activation_key`: Activation key, required if activating a subscription
- `baseline_redhat_org_id`: RedHat organization ID, required if activating a subscription
- `baseline_redhat_repos`: Additional repos to enable (for example, `codeready-builder-for-rhel-9-x86_64-rpms`), defaults to `[]`
- `baseline_rhel_syspurpose_usage`: System usage, defaults to `Development/Test`
- `baseline_rhel_syspurpose_role`: System role, defaults to `RHEL Server`
- `baseline_rhel_syspurpose_service_level_agreement`: System SLA, defaults to `Self-Support`

Some of these (probably activation key and org ID) should be set in an [Ansible vault file](https://docs.ansible.com/ansible/latest/vault_guide/vault_encrypting_content.html#encrypting-files-with-ansible-vault) or stored in another secrets manager. For example:

```sh
ansible-vault create rhel_secrets.yml
```

## Example

```yaml
---
- name: Apply baseline configuration
  ansible.builtin.include_role:
    name: brianreumere.server.baseline
  vars:
    baseline_install_qemu_guest_agent: true
    baseline_allowed_ports:
      - port: 22
        proto: tcp
      - port: 80
        proto: tcp
      - port: 443
        proto: tcp
```
