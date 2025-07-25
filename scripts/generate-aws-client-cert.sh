#!/bin/bash
# AWS IAM Roles Anywhere Client Certificate Generator
# Usage: ./generate-aws-client-cert.sh -n <name> [options]

set -euo pipefail

# Default values
OUTPUT_DIR="./certs"
CFSSL_API="http://127.0.0.1:8888"
CA_CERT="/var/lib/cfssl/intermediate.pem"
CA_KEY="/var/lib/cfssl/intermediate-key.pem"
CONFIG="/etc/cfssl/ca-config.json"
USE_API=false
ORGANIZATION="SWN Lab"
ORGANIZATIONAL_UNIT="HOME LAB"
COUNTRY="CA"
STATE="Ontario"
LOCALITY="Toronto"
EMAIL=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Generate AWS IAM Roles Anywhere compatible client certificates

OPTIONS:
    -n, --name NAME         Certificate name (required)
    -e, --email EMAIL       Email address for the certificate subject
    -o, --output DIR        Output directory [default: ./certs]
    -a, --api               Use CFSSL API instead of local files
    -u, --api-url URL       CFSSL API URL [default: http://127.0.0.1:8888]
    --org ORG              Organization [default: SWN Lab]
    --ou OU                Organizational Unit [default: HOME LAB]
    --country COUNTRY      Country [default: CA]
    --state STATE          State/Province [default: Ontario]
    --city CITY            City/Locality [default: Toronto]
    --help                 Show this help message

EXAMPLES:
    # Generate basic client certificate
    $0 -n aws-client
    
    # Generate client certificate with email
    $0 -n aws-client -e user@example.com
    
    # Generate client certificate using API
    $0 -n aws-client -a
    
    # Generate client certificate with custom organization
    $0 -n aws-client --org "My Company"

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--name)
            CERT_NAME="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -a|--api)
            USE_API=true
            shift
            ;;
        -u|--api-url)
            CFSSL_API="$2"
            shift 2
            ;;
        --org)
            ORGANIZATION="$2"
            shift 2
            ;;
        --ou)
            ORGANIZATIONAL_UNIT="$2"
            shift 2
            ;;
        --country)
            COUNTRY="$2"
            shift 2
            ;;
        --state)
            STATE="$2"
            shift 2
            ;;
        --city)
            LOCALITY="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "${CERT_NAME:-}" ]]; then
    log_error "Certificate name is required (-n|--name)"
    usage
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

log_info "Generating AWS IAM Roles Anywhere client certificate: $CERT_NAME"
log_info "Certificate will meet AWS IAM Roles Anywhere requirements:"
log_info "  - CA:FALSE in Basic Constraints"
log_info "  - Digital Signature in Key Usage"
log_info "  - Client Authentication in Extended Key Usage"
log_info "  - SHA256 or stronger signing algorithm"

# Create CSR configuration
CSR_FILE="$OUTPUT_DIR/${CERT_NAME}-csr.json"

# Build the names section with optional email
NAMES_SECTION='{
      "C": "'$COUNTRY'",
      "ST": "'$STATE'",
      "L": "'$LOCALITY'",
      "O": "'$ORGANIZATION'",
      "OU": "'$ORGANIZATIONAL_UNIT'"'

if [[ -n "$EMAIL" ]]; then
    NAMES_SECTION+=',
      "E": "'$EMAIL'"'
fi

NAMES_SECTION+='
    }'

cat > "$CSR_FILE" << EOF
{
  "CN": "$CERT_NAME",
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    $NAMES_SECTION
  ],
  "hosts": [
    "$CERT_NAME"
  ]
}
EOF

log_info "Created CSR configuration: $CSR_FILE"

# Generate certificate
if [[ "$USE_API" == "true" ]]; then
    log_info "Using CFSSL API at $CFSSL_API"
    
    # Check if API is available
    if ! curl -s "$CFSSL_API/api/v1/cfssl/health" > /dev/null; then
        log_error "CFSSL API is not available at $CFSSL_API"
        exit 1
    fi
    
    # Generate certificate via API
    RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
        -d @"$CSR_FILE" \
        "$CFSSL_API/api/v1/cfssl/newcert?profile=client")
    
    if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
        echo "$RESPONSE" | jq -r '.result.certificate' > "$OUTPUT_DIR/${CERT_NAME}.pem"
        echo "$RESPONSE" | jq -r '.result.private_key' > "$OUTPUT_DIR/${CERT_NAME}-key.pem"
        log_success "Certificate generated via API"
    else
        log_error "API request failed: $(echo "$RESPONSE" | jq -r '.errors[0].message // "Unknown error"')"
        exit 1
    fi
else
    log_info "Using local CFSSL files"
    
    # Check if required files exist
    if [[ ! -f "$CA_CERT" ]] || [[ ! -f "$CA_KEY" ]] || [[ ! -f "$CONFIG" ]]; then
        log_error "Required CA files not found. Make sure CFSSL is properly installed."
        log_error "Expected files: $CA_CERT, $CA_KEY, $CONFIG"
        exit 1
    fi
    
    # Generate certificate using local files
    cd "$OUTPUT_DIR"
    cfssl gencert \
        -ca "$CA_CERT" \
        -ca-key "$CA_KEY" \
        -config "$CONFIG" \
        -profile client \
        "${CERT_NAME}-csr.json" | cfssljson -bare "$CERT_NAME"
    
    log_success "Certificate generated using local CA"
fi

# Set proper permissions
chmod 600 "$OUTPUT_DIR/${CERT_NAME}-key.pem"
chmod 644 "$OUTPUT_DIR/${CERT_NAME}.pem"

# Display certificate information
log_success "Certificate files generated:"
echo "  Certificate: $OUTPUT_DIR/${CERT_NAME}.pem"
echo "  Private Key: $OUTPUT_DIR/${CERT_NAME}-key.pem"
echo "  CSR Config:  $OUTPUT_DIR/${CERT_NAME}-csr.json"

# Verify certificate
log_info "Certificate details:"
cfssl-certinfo -cert "$OUTPUT_DIR/${CERT_NAME}.pem" | jq -r '.subject, .sans, .not_before, .not_after'

# Verify AWS IAM Roles Anywhere compatibility
log_info "Verifying AWS IAM Roles Anywhere compatibility..."
CERT_INFO=$(openssl x509 -in "$OUTPUT_DIR/${CERT_NAME}.pem" -noout -text)

# Check Basic Constraints
if echo "$CERT_INFO" | grep -q "CA:TRUE"; then
    log_error "Certificate has CA:TRUE - AWS IAM Roles Anywhere requires CA:FALSE"
    log_error "Certificate is NOT compatible with AWS IAM Roles Anywhere"
    exit 1
elif echo "$CERT_INFO" | grep -q "CA:FALSE"; then
    log_success "✓ Certificate has CA:FALSE"
else
    log_warning "Basic Constraints not found - this may be acceptable"
fi

# Check Extended Key Usage
if echo "$CERT_INFO" | grep -q "TLS Web Client Authentication"; then
    log_success "✓ Certificate has Client Authentication usage"
else
    log_error "Certificate missing Extended Key Usage: Client Authentication"
    log_error "Certificate is NOT compatible with AWS IAM Roles Anywhere"
    exit 1
fi

# Check Key Usage
if echo "$CERT_INFO" | grep -A5 "Key Usage:" | grep -q "Digital Signature"; then
    log_success "✓ Certificate has Digital Signature usage"
else
    log_error "Certificate missing Digital Signature usage"
    log_error "Certificate is NOT compatible with AWS IAM Roles Anywhere"
    exit 1
fi

# Check signature algorithm
if echo "$CERT_INFO" | grep -q "Signature Algorithm: sha256"; then
    log_success "✓ Certificate uses SHA256 or stronger signing algorithm"
else
    log_warning "Certificate may not use SHA256 or stronger signing algorithm"
    log_warning "Check signature algorithm: $(echo "$CERT_INFO" | grep "Signature Algorithm:" | head -1)"
fi

log_success "Certificate generation completed!"
log_success "Certificate appears to be compatible with AWS IAM Roles Anywhere"

# Cleanup option
read -p "Remove CSR configuration file? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm "$CSR_FILE"
    log_info "CSR configuration file removed"
fi
