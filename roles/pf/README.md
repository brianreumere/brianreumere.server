# pf

## Overview

Configures a [pf](https://www.openbsd.org/faq/pf/)-based firewall/router on OpenBSD. Optionally sets up additional services like DHCP and DNS.

The pf ruleset is built around an inbound default deny policy and a `pass out` rule that allows all outbound traffic on all interfaces (with some exceptions like traffic out the egress interface to non-internet-routable IP address ranges and optionally misbehaving/blocked addresses). Traffic to internet-routable IP ranges is also allowed in on all VLAN and remote access VPN interfaces.

Some other sensible things like antispoof rules and NAT (overload NAT or PAT, in Cisco terms) on the egress interface are hardcoded.

The main variables that control how traffic is allowed in on interfaces and where it is allowed to go (e.g., other IP addresses or subnets) are `pf_hosts`, `subnets`, `s2s_vpns`, `ra_vpns`, and `open_ports`. Each of these are described in more detail in [Variable schemas](#variable-schemas).

Any references to VPN (remote access or site-to-site) interfaces refer to Wireguard (`wg`) interfaces.

## Variables

### Required

- `pf_physical_ifs`: Physical network interfaces to configure, each dict item is just the contents of the `hostname.if` file that will be created for the interface:
```yaml
      em0: |
        description "Internet"
        dhcp
      em1: |
        description "Internal"
        inet 172.16.1.1 255.255.255.0
        up
```
- `pf_egress_if`: The physical network interface that is connected to the internet
- `subnets`: See [Subnets](#subnets)
- `pf_hosts`: See [Hosts](#hosts)
- `internal_dns_zone`: The domain to use for your internal DNS zone
- `dns_reverse_zone`: The zone to serve reverse DNS (PTR) records for, for example `16.172.in-addr.arpa` if you want to serve records for the range `172.16.0.0/16`
- `pf_management_ip`: The internal management IP address of the pf router (will be used as the DNS A record)
- `dns_reverse_octets`: Number of octets of a host IP to use for the host's PTR record
- `dns_soa_master`: The hostname to use in the DNS SOA record (usually matches the pf router's full hostname)
- `dns_soa_email`: The email address to use in the DNS SOA record
- `dns_ns`: A list of hostnames to use for DNS NS records (can typically just include the pf router's full hostname)
- `pf_full_cidr`: The full CIDR block you want to use for internal networks (used to determine what Unbound considers private addresses)

### Optional

- `ra_vpns`: Wireguard remote access VPNs, see [Remote access VPNs](#remote-access-vpns), defaults to `[]`
- `s2s_vpns`: Wireguard site-to-site VPNs, see [Site-to-site VPNs](#site-to-site-vpns), defaults to `[]`
- `tables`: pf tables, see [Tables](#tables), defaults to `[]`
- `open_ports`: A list of ports to open on the egress interface and optionally redirect to another host, see [Open ports](#open-ports)
- `pf_default_rdomain`: The default routing domain (used by subnet `hide_behind` functionality), defaults to `0`
- `dns_enabled`: Whether Unbound is configured to recursively resolve hostnames and NSD is configured as an authoritative nameserver for your internal domain, defaults to `true`
- `dhcpd_enabled`: Whether dhcpd is configured to give out DHCP leases, defaults to `true`
- `authpf_message`: The contents to insert into the `authpf.message` file (to be displayed when authpf users authenticate via SSH)

## Variable schemas

### Subnets

Each key in the `subnets` variable is just a unique name to refer to the subnet by. It might closely match the `desc` (description) value, but doesn't have to. An example is below, followed by an explanation of each sub-item. Note that this example is not a working example, and some values are present just to demonstrate what is possible.

```yaml
    subnets:
      servers:
        cidr: 172.16.0.0/24
        desc: Servers
        vlan: 10
        vpif: em1
        hide_behind: some_vpn
        services:
          dns:
          dhcp:
            range: 172.17.10.128/26
            add:
              - "# Custom DNS"
              - "option domain-name-servers 4.2.2.2";
          ping:
          ssh:
        allow:
          - port: 22
            proto: tcp
            from:
              - name: guest_wifi
                type: subnet
              - name: macbook
                type: host
                subnet: wifi
```

- `cidr` is the CIDR block of the subnet
- `desc` is a description of the subnet
- `vlan` is either a VLAN number or `false` to indicate that a VLAN interface should not be created for the subnet (VLAN interfaces will always use the first usable IP address of the subnet)
- `vpif` is the VLAN's parent physical interface, if `vlan` is set to a VLAN number
- `hide_behind` is an optional setting that allows you to route all traffic from a subnet over a site-to-site VPN (must match a key in `s2s_vpns`)
- `services` is a list of dicts (keys are service names, and they can generally just be empty dicts) that are provided **on** the subnet (to hosts that are on that subnet); valid dict keys are `dns`, `dhcp`, `ping`, and `ssh` (these affect whether services like `unbound`, `dhcpd`, and `ssh` listen on interfaces in the subnet, and whether other traffic like ICMP echo requests is allowed; some values are hardcoded in the `pf.conf` template, so you can't add arbitrary service names here unless you account for them in `pf.conf.j2`!)
    - `dhcp` accepts the `range` (CIDR block that defines the range of addresses leased by dhcpd) and `add` (list of custom lines to add to the subnet's configuration in `dhcpd.conf`) items
- `allow` follows the same format as in the `pf_hosts` variable

### Hosts

Each key in the `pf_hosts` variable is a short hostname, e.g., `nas` for a network attached storage device. An example item from the `pf_hosts` dict is below, followed by an explanation of each sub-item.

```yaml
    pf_hosts:
      nas:
        ip:      172.16.0.5/24
        ptr:     true
        res:     36:6e:f0:6a:43:2a
        isolate: false
        allow:
          - port:  "{ 139, 445 }"
            proto: tcp
            from:
              - name:   laptop
                type:   host
                subnet: my_vpn
              - name:   wifi
                type:   subnet
          - port:  "0:65535"
            proto: "{ tcp udp }"
            from:
              - name: authpf_users
                type: table
          - port:  echoreq
            proto: icmp
            from:
              - name:   authpf_users
                type:   table
                subnet: my_vpn
              - name:   authpf_users
                type:   table
                subnet: wifi
```

- `ip` is the IP address of the host, and affects DNS records, DHCP reservations, and pf rules
- `ptr` is a boolean that controls whether a DNS PTR record is created for the host
- `res` is the MAC address of the host and, if provided, creates a DHCP reservation
- `isolate` is an optional boolean; when set to `true` it blocks all traffic originating **from** the host
- `allow` is a list of `port` and `proto` (protocol) combinations (these should be strings formatted any way that that is valid for [`pf.conf`](https://man.openbsd.org/pf.conf)) to allow (if `proto` is `icmp` then `port` should specify ICMP types like `echoreq` instead of port numbers) from a list of hosts or subnets in the `from` list; `name` should refer to a host, subnet, or table key in the `pf_hosts`, `subnets`, or `tables` dict, respectively, and `type` should indicate whether the item refers to a host, subnet, or table; if `type` is `host`, `subnet` is also required to indicate which subnet the host is a part of (note that pf syntax like `{ macro1 macro2 }` is **not** valid in any fields other than `port` and `proto`)

### Remote access VPNs

```
    ra_vpns:
      my_vpn:
        if:      wg7
        rdomain: 0
        subnet:  my_vpn_subnet
```

- `if` is the `wg` interface of the VPN
- `rdomain` is the routing domain that is used by the VPN
- `subnet` is the subnet associated with VPN clients

The key of the VPN dict must also match a key in the `subnets` variable (to configure a subnet that remote access VPN users will be on).

If any remote access VPNs are configured, you must create a `ra_vpn_secrets` dict with a key corresponding to each key in the `ra_vpns` dict. These secret values specify your Wireguard private key and all peers' public keys. For example, set the following in an [Ansible vault file](https://docs.ansible.com/ansible/latest/vault_guide/vault_encrypting_content.html#encrypting-files-with-ansible-vault):

```yaml
ra_vpn_secrets:
  my_vpn:
    wgkey: '<private key>'
    peers:
      - name: Laptop
        key:  '<laptop public key>'
        ip:   172.16.2.2/32
      - name: Phone
        key:  '<phone public key>'
        ip:   172.16.2.3/32
```

### Site-to-site VPNs

```yaml
    s2s_vpns:
      some_vpn:
        if:       wg9
        dns:      10.0.0.1
        rdomain:  9
        block_in: true
        open:
          - port:   3000
            proto:  tcp
            rdr_to: some_host
```

- `if` is the `wg` interface of the VPN
- `dns` is a DNS server IP address that is allowed to be routed over the VPN
- `rdomain` is the routing domain that is used by the VPN
- `block_in` is an optional setting that will block any incoming traffic on the VPN interface
- `open` is an optional list of traffic that is allowed in on the VPN interface

If any site-to-site VPNs are configured, a corresponding key in the `s2s_vpn_secrets` dict must exist. These should be set in an [Ansible vault file](https://docs.ansible.com/ansible/latest/vault_guide/vault_encrypting_content.html#encrypting-files-with-ansible-vault):

```yaml
s2s_vpn_secrets:
  some_vpn:
    wgkey: '<private key>'
    wgpeer: '<peer public key>'
    wgendpoint: '<endpoint URL> <endpoint port>'
    wgaip: <IPs to route over VPN>
    wgpsk: '<PSK>'
    wgpka: <PKA>
    ip: <IP address>
```

### Tables

```yaml
    tables:
      brutes:
        desc: IPs that try to brute force things
        type: block
      authpf_users:
        desc: Some users to allow via authpf
        type: authpf
        users:
          - some_new_user
```

- `desc` is a description of the table
- `type` is `block` (addresses in a `block` table will be blocked on the egress interface and site-to-site VPN interfaces with `block_in` set to `true`) or `authpf` (if any tables of this type exist, some setup of authpf will be done, and any usernames listed in the `users` will be created and assigned to the `authpf` login class)

### Open ports

```yaml
    open_ports:
      - port:       80
        proto:      tcp
        rdr_to:     www_server
        rate_limit: true
        rl_table:   bad_ips
```

- `port` is the port allowed in on the egress interface
- `proto` is the allowed protocol
- `rdr_to` is optional, and is the host where the traffic is redirected to
- `rate_limit` optionally adds addresses that exceed some threshold to a table that is blocked
- `rl_table` is the name of the table

## Example

This is a barebones example that does not include any VPNs, pf tables, or forwarded/open ports.

```yaml
- name: Set up pf
  ansible.builtin.include_role:
    name: brianreumere.server.pf
  vars:
    pf_physical_ifs:
      em0: |
        description "Egress"
        dhcp
      em1: |
        description "Internal"
        inet 10.0.0.1 255.255.255.0
        up
    pf_egress_if: em0
    subnets:
      internal:
        cidr: 10.0.0.0/24
        desc: My internal subnet
        vlan: false
        phys: em1
        services:  # Services to allow internally to the subnet
          dns:
          dhcp:
          ping:
          ssh:
    pf_hosts:
      my_router:
        ip: 10.0.0.1/24
        ptr: true
        allow:
          - port: 22
            proto: tcp
            from:
              - name: internal
                type: subnet
      my_laptop:
        ip:  10.0.0.2/24
        res: 9e:17:5f:42:cc:f2
        ptr: true
    internal_dns_zone: mylan.foo
    dns_reverse_zone: 0.0.10.in-addr.arpa
    pf_management_ip: 10.0.0.1
    dns_reverse_octets: 3
    dns_soa_master: my_router.mylan.foo
    dns_soa_email: me@example.org
    dns_ns:
      - my_router.mylan.foo
    pf_full_cidr: 10.0.0.0/16  # Just in case we want to set up more subnets in the future
```
