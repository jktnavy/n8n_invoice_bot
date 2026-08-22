# Environment Discovery

No production VPS has been accessed from this workspace yet.

Local read-only discovery on this WSL session found:

```text
OS: Ubuntu 24.04.4 LTS on WSL2
RAM: 15 GiB total, 13 GiB available at discovery time
Swap: 4 GiB
Disk: /dev/sdd 1007G total, 896G available
Node: v22.23.2
npm: 10.9.8
Python: 3.13.13
MySQL/MariaDB client: MariaDB 10.11.14
Nginx: 1.24.0
Docker: not visible in this Codex shell at prior validation time
```

Ports already listening locally included:

```text
80
22
3306
5432
6379
631
```

Production deployment must repeat discovery on the actual VPS before changing services.

