# CFSSL Certificate Authority Ansible Role

This role installs and configures [CFSSL](https://github.com/cloudflare/cfssl), CloudFlare's PKI/TLS toolkit, to create a Certificate Authority (CA) for your homelab infrastructure.

## Features

- Installs CFSSL binaries from official GitHub releases
- Creates Root CA and Intermediate CA certificates
- Configures CFSSL API server for certificate issuance
- Sets up systemd service for automatic startup
- Implements security best practices with dedicated user
- Automated backup system with retention policy
- Multiple certificate profiles (server, client, peer)

## Requirements

- Ubuntu/Debian system
- Internet connection for downloading CFSSL binaries
- Sufficient entropy for key generation
- At least 1GB RAM recommended

## Role Variables

### CA Configuration

- `ca_common_name`: Root CA common name (default: "SWN Lab Root CA")
- `ca_organization`: Organization name (default: "SWN Lab")
- `ca_organizational_unit`: Organizational unit (default: "IT Department")
- `ca_country`: Country code (default: "US")
- `ca_state`: State/Province (default: "California")
- `ca_locality`: City/Locality (default: "San Francisco")
- `ca_expiry`: Root CA expiry (default: "87600h" - 10 years)
- `ca_key_algorithm`: Key algorithm (default: "rsa")
- `ca_key_size`: Key size (default: 4096)

### Intermediate CA

- `intermediate_ca_common_name`: Intermediate CA name (default: "SWN Lab Intermediate CA")
- `intermediate_ca_expiry`: Intermediate CA expiry (default: "43800h" - 5 years)

### API Server

- `cfssl_api_enabled`: Enable API server (default: true)
- `cfssl_api_port`: API server port (default: 8888)
- `cfssl_api_bind_address`: Bind address (default: "127.0.0.1")
- `cfssl_api_log_level`: Log level (default: "info")

### Paths and Security

- `cfssl_install_dir`: Binary installation directory (default: "/usr/local/bin")
- `cfssl_config_dir`: Configuration directory (default: "/etc/cfssl")
- `cfssl_data_dir`: Data directory (default: "/var/lib/cfssl")
- `cfssl_user`: Service user (default: "cfssl")
- `cfssl_group`: Service group (default: "cfssl")

## Certificate Profiles

The role creates three certificate profiles:

- **server**: For server certificates (TLS server authentication)
- **client**: For client certificates (TLS client authentication)
- **peer**: For peer certificates (both server and client authentication)

## Usage

### Basic Installation

```yaml
- hosts: ca_server
  roles:
    - cfssl
```

### Custom Configuration

```yaml
- hosts: ca_server
  vars:
    ca_common_name: "My Company Root CA"
    ca_organization: "My Company"
    cfssl_api_bind_address: "0.0.0.0" # Allow external access
  roles:
    - cfssl
```

## Post-Installation

### Access the CA

- **Root CA Certificate**: `/var/lib/cfssl/ca.pem`
- **Intermediate CA Certificate**: `/var/lib/cfssl/intermediate.pem`
- **API Server**: `http://127.0.0.1:8888` (if enabled)

### Issue a Server Certificate

1. Create a CSR configuration file:

```json
{
  "CN": "example.com",
  "hosts": ["example.com", "www.example.com", "172.16.10.100"],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "US",
      "ST": "California",
      "L": "San Francisco",
      "O": "My Company",
      "OU": "IT Department"
    }
  ]
}
```

2. Generate the certificate:

```bash
cfssl gencert \
  -ca /var/lib/cfssl/intermediate.pem \
  -ca-key /var/lib/cfssl/intermediate-key.pem \
  -config /etc/cfssl/ca-config.json \
  -profile server \
  server-csr.json | cfssljson -bare server
```

### Using the API Server

```bash
# Generate certificate via API
curl -X POST -H "Content-Type: application/json" \
  -d @server-csr.json \
  http://127.0.0.1:8888/api/v1/cfssl/newcert
```

## Security Considerations

- Root CA private key is stored on disk - consider offline storage
- API server binds to localhost by default for security
- Dedicated user account with minimal privileges
- Regular backups with encryption recommended
- Monitor certificate expiration dates
- Implement proper firewall rules

## Backup and Recovery

### Automatic Backups

The role creates daily backups at 2 AM with 30-day retention:

- Backup location: `/backup/cfssl/`
- Backup format: `cfssl_backup_YYYYMMDD_HHMMSS.tar.gz`
- Includes all certificates, keys, and configuration

### Manual Backup

```bash
/usr/local/bin/backup-cfssl.sh
```

### Recovery

```bash
# Extract backup
cd /backup/cfssl
tar -xzf cfssl_backup_YYYYMMDD_HHMMSS.tar.gz

# Restore files
sudo cp -r cfssl_backup_YYYYMMDD_HHMMSS/* /var/lib/cfssl/
sudo chown -R cfssl:cfssl /var/lib/cfssl
sudo systemctl restart cfssl
```

## Troubleshooting

### Service Issues

```bash
# Check service status
sudo systemctl status cfssl

# View logs
sudo journalctl -u cfssl -f

# Test API
curl http://127.0.0.1:8888/api/v1/cfssl/health
```

### Certificate Issues

```bash
# View certificate details
cfssl-certinfo -cert /var/lib/cfssl/ca.pem

# Verify certificate chain
openssl verify -CAfile /var/lib/cfssl/ca.pem /var/lib/cfssl/intermediate.pem
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R cfssl:cfssl /var/lib/cfssl /etc/cfssl
sudo chmod 700 /var/lib/cfssl /etc/cfssl
sudo chmod 600 /var/lib/cfssl/*.pem /var/lib/cfssl/*-key.pem
```

## Integration with Other Services

### Nginx Proxy Manager

Use the generated certificates with Nginx Proxy Manager for internal SSL termination.

### Keycloak

Configure Keycloak to use certificates issued by your CA for HTTPS.

### Service Mesh

Use the CA for issuing certificates in a service mesh architecture.

## License

This role is provided as-is for educational and personal use.
