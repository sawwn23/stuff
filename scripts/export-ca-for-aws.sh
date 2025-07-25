#!/bin/bash
# Export CA Certificate for AWS IAM Roles Anywhere
# Usage: ./export-ca-for-aws.sh

set -euo pipefail

# Default values
CA_CERT="/var/lib/cfssl/ca.pem"
INTERMEDIATE_CA_CERT="/var/lib/cfssl/intermediate.pem"
OUTPUT_DIR="./certs"

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

# Create output directory
mkdir -p "$OUTPUT_DIR"

log_info "Exporting CA certificates for AWS IAM Roles Anywhere"

# Check if CA certificates exist
if [[ ! -f "$CA_CERT" ]]; then
    log_error "Root CA certificate not found: $CA_CERT"
    exit 1
fi

if [[ ! -f "$INTERMEDIATE_CA_CERT" ]]; then
    log_error "Intermediate CA certificate not found: $INTERMEDIATE_CA_CERT"
    exit 1
fi

# Copy CA certificates to output directory
cp "$CA_CERT" "$OUTPUT_DIR/root-ca.pem"
cp "$INTERMEDIATE_CA_CERT" "$OUTPUT_DIR/intermediate-ca.pem"

log_success "CA certificates exported to $OUTPUT_DIR"

# Create a combined CA certificate chain
cat "$INTERMEDIATE_CA_CERT" "$CA_CERT" > "$OUTPUT_DIR/ca-chain.pem"
log_success "Combined CA chain created: $OUTPUT_DIR/ca-chain.pem"

# Display certificate information
log_info "Root CA certificate details:"
openssl x509 -in "$OUTPUT_DIR/root-ca.pem" -noout -text | grep -A1 "Subject:" | head -2
openssl x509 -in "$OUTPUT_DIR/root-ca.pem" -noout -text | grep -A1 "Issuer:" | head -2
openssl x509 -in "$OUTPUT_DIR/root-ca.pem" -noout -text | grep "CA:" | head -1

log_info "Intermediate CA certificate details:"
openssl x509 -in "$OUTPUT_DIR/intermediate-ca.pem" -noout -text | grep -A1 "Subject:" | head -2
openssl x509 -in "$OUTPUT_DIR/intermediate-ca.pem" -noout -text | grep -A1 "Issuer:" | head -2
openssl x509 -in "$OUTPUT_DIR/intermediate-ca.pem" -noout -text | grep "CA:" | head -1

# Verify certificate chain
log_info "Verifying certificate chain..."
if openssl verify -CAfile "$OUTPUT_DIR/root-ca.pem" "$OUTPUT_DIR/intermediate-ca.pem" > /dev/null 2>&1; then
    log_success "Certificate chain verification successful"
else
    log_error "Certificate chain verification failed"
    openssl verify -CAfile "$OUTPUT_DIR/root-ca.pem" "$OUTPUT_DIR/intermediate-ca.pem"
    exit 1
fi

log_info "For AWS IAM Roles Anywhere, you should register:"
log_info "- For a 2-tier PKI (recommended): $OUTPUT_DIR/intermediate-ca.pem"
log_info "- For a single-tier PKI: $OUTPUT_DIR/root-ca.pem"
