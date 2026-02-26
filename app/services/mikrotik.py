from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouterAssignment:
    subnet_cidr: str
    gateway_ip: str
    customer_ip: str


def assign_point_to_point_block(customer_id: int) -> RouterAssignment:
    bucket = customer_id // 120
    third_octet = 10 + bucket
    base = (customer_id % 120) * 2

    network = f"10.20.{third_octet}.{base}"
    gateway_ip = f"10.20.{third_octet}.{base + 1}"
    customer_ip = f"10.20.{third_octet}.{base + 2}"
    return RouterAssignment(subnet_cidr=f"{network}/30", gateway_ip=gateway_ip, customer_ip=customer_ip)


def build_mikrotik_script(
    *,
    customer_name: str,
    router_identity: str,
    wan_interface: str,
    lan_interface: str,
    gateway_ip: str,
    customer_ip: str,
) -> str:
    return "\n".join(
        [
            f"/system identity set name=\"{router_identity}\"",
            f"/interface ethernet set [find default-name={wan_interface}] name={wan_interface}",
            f"/interface ethernet set [find default-name={lan_interface}] name={lan_interface}",
            f"/ip address add address={customer_ip}/30 interface={wan_interface} comment=\"NetNova {customer_name} WAN\"",
            f"/ip route add dst-address=0.0.0.0/0 gateway={gateway_ip} comment=\"NetNova upstream\"",
            f"/ip firewall nat add chain=srcnat out-interface={wan_interface} action=masquerade comment=\"NetNova NAT\"",
            f"/ip dns set servers={gateway_ip},1.1.1.1 allow-remote-requests=yes",
            "/ip service set [find name=www] disabled=yes",
            "/ip service set [find name=telnet] disabled=yes",
            "/ip service set [find name=ftp] disabled=yes",
        ]
    )
