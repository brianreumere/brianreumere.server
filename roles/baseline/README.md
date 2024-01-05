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

### Required


### Optional

- `upgrade_packages`: Whether the role should run a package upgrade, defaults to `false` (can be useful to set to `true` on the initial application of the role)
- `install_qemu_guest_agent`: Whether the QEMU guest agent should be installed, defaults to `false`
- `enable_firewall`: Whether to enable a firewall, defaults to `true`

## Example

```yaml
---
- name: Install shiori
  ansible.builtin.include_role:
    name: brianreumere.software.shiori
  vars:
    shiori_hostname: shiori.example.net
```
