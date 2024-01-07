# kvm

## Overview

Installs and configures KVM/libvirt on RHEL with bridged network connectivity and directory-based storage pools. Copies a useful [cloud-config](https://cloudinit.readthedocs.io/en/latest/explanation/format.html#user-data-formats-cloud-config) file to the server to help with provisioning VMs. Optionally configures backups with [virtnbdbackup](https://github.com/abbbi/virtnbdbackup) and backup uploads to S3-compatible object storage (e.g., DigitalOcean Spaces).

This role assumes you have two network interfaces, one for management traffic and one for virtual network traffic. It also assumes you want to configure bridge interfaces for VM network connectivity.

## Variables

### Required

`kvm_management_if`: The management network interface
`kvm_management_ip`: The IP address to configure on the management interface (including prefix)
`kvm_management_gw`: The default gateway IP to configure on the management interface
`kvm_management_dns`: A list of DNS servers to configure on the management interface
`kvm_virt_if`: The network interface for VM traffic
`kvm_vlans`: A list of VLAN interfaces to create, for example:
```yaml
      - vlan_id: 200
        bridge: br200
        parent_dev: "{{ kvm_virt_if }}"
        name: Servers
```
`kvm_nonroot_user`: A nonroot user you log into the KVM server with (should already exist)
`kvm_parent_dir`: The parent directory for storage pools and other VM-related files (will be created under `/`)
`kvm_dir_pools`: A list of directories to create for libvirt storage pools, for example:
```yaml
      - pool_name: vms
        path: /libvirt/vms
```
`kvm_cloud_config_authorized_key`: The SSH key to place in the cloud-config file (useful for creating VMs)
`kvm_cloud_config_user`: The user to create on VMs launched with the cloud-config script
`kvm_cloud_config_initial_password`: The initial password for users created on VMs launched with the cloud-config script, should be stored in an [Ansible vault file](https://docs.ansible.com/ansible/latest/vault_guide/vault_encrypting_content.html#encrypting-files-with-ansible-vault) or other secrets manager (it will be stored in plain text in the cloud-config script on the KVM host, and should be reset by logging into any VMs provisioned using the script)

For each directory configured in `kvm_dir_pools`, you must manually create the directory pool. For example:

```sh
virsh pool-define-as --name vms --type dir --target /libvirt/vms
```

#### Backups

If `kvm_backups_enabled` is `true`, some additional configuration is required.

The following variables should be set in an [Ansible vault file](https://docs.ansible.com/ansible/latest/vault_guide/vault_encrypting_content.html#encrypting-files-with-ansible-vault). These will be added to the root user's `.bash_profile` and used to upload backup files to an S3 bucket:

```yaml
s3_region: '<S3 region>'
s3_bucket: '<S3 bucket>'
s3_endpoint: '<S3 endpoint>'
s3_access_key: '<S3 access key>'
s3_secret_key: '<S3 secret key>'
s3_sse_key: '<SSE key>'
s3_sse_key_md5: '<SSE key MD5 hash>'
```

You also need to set `kvm_local_backup_path` to the directory where local backups should be created, `kvm_backups_cron_minute` to the minute of the hour the daily backup job should run, and `kvm_backups_cron_hour` to the hour the daily backup job should run.

To configure which VMs to back up, set `kvm_domains_to_backup`. For example:

```yaml
    kvm_domains_to_backup:
      vm1:
        - vda
      vm2:
        - vda
        - vdb
```

Differential backups are hardcoded to run daily at the time you specify. To configure how many daily backups are kept locally, set the `kvm_keep_dailies` variable. The offload script will delete backups older than the configured number of days. To control which backups are uploaded to S3, set the `kvm_upload_days_of_month` list. For example, to upload backups that occur on the 14th and 28th of every month:

```yaml
    kvm_upload_days_of_month:
      - 14
      - 28
```

### Optional

`kvm_backups_enabled`: Whether to enable scheduled backups, defaults to `false`
`kvm_pci_passthrough`: Whether to enable PCI passthrough kernel modules, defaults to `true`

## Example

```yaml
---
- name: Set up KVM/libvirt
  ansible.builtin.include_role:
    name: brianreumere.server.kvm
  vars:
    kvm_management_if: eno1
    kvm_management_ip: 10.0.0.3/24
    kvm_management_gw: 10.0.0.1
    kvm_management_dns:
      - 10.0.0.1
    kvm_virt_if: eno2
    kvm_vlans:
      - vlan_id: 100
        bridge: br100
        parent_dev: "{{ kvm_virt_if }}"
        name: Web servers
      - vlan_id: 200
        bridge: br200
        parent_dev: "{{ kvm_virt_if }}"
        name: Other servers
    kvm_nonroot_user: your_username
    kvm_cloud_config_user: vm_user
    kvm_cloud_config_authorized_key: ssh-rsa …
    kvm_parent_dir: /libvirt
    kvm_dir_pools:
      - pool_name: vms
        path: /libvirt/vms
      - pool_name: base
        path: /libvirt/base
    kvm_backups_enabled: true
    kvm_domains_to_backup:
      vm1:
        - vda
      vm2:
        - vda
        - vdb
    kvm_local_backup_path: /libvirt/backups
    kvm_backups_cron_minute: 0
    kvm_backups_cron_hour: 8
    kvm_upload_days_of_month:
      - 1
    kvm_keep_dailies: 7
```

To launch VMs using the included cloud-config script, first download a base cloud image. For example, `jammy-server-cloudimg-amd64-disk-kvm.img` from [https://cloud-images.ubuntu.com/jammy/current/](https://cloud-images.ubuntu.com/jammy/current/). Create a 50 GB volume based on the image:

```sh
qemu-img create -f qcow2 -F qcow2 -b /images/base/jammy-server-cloudimg-amd64-disk-kvm.img /libvirt/vms/vm1.qcow2
qemu-img resize /images/vms/vm1.qcow2 50G
```

Run `virt-install`. Be sure to log in with the password set in `kvm_cloud_config_initial_password` and set a new secure password on the VM after it launches (you can do so through the virtual console accessible with `virsh console`).

```sh
virt-install \
    --import \
    --osinfo ubuntu22.04 \
    --autostart \
    --name vm1 \
    --memory 2048 \
    --vcpus 4,cpuset=auto \
    --cpu host \
    --disk path=/libvirt/vms/vm1.qcow2,format=qcow2,bus=virtio \
    --network bridge=br100,model=virtio \
    --autoconsole none \
    --cloud-init disable=on,user-data=/home/your_username/virt/cloud-config-baseline.yaml
```
