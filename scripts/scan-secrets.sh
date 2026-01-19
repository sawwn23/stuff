#!/bin/bash
# Secret Scanning Script
# This script helps identify potential secrets in the codebase

set -e

echo "🔍 Secret Scanning Tool"
echo "======================"
echo ""

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Track findings
FINDINGS=0

# Function to check for secrets
check_secrets() {
    local file=$1
    local line_num=0
    
    while IFS= read -r line; do
        ((line_num++))
        
        # Check for hardcoded API keys, tokens, passwords
        if echo "$line" | grep -qiE "(api[_-]?key|apikey|secret|password|token|auth|credential|private[_-]?key)\s*=\s*['\"][^'\"]{10,}['\"]"; then
            echo -e "${RED}⚠️  Found potential secret in $file:${NC}"
            echo -e "${YELLOW}   Line $line_num:${NC} ${line:0:100}..."
            ((FINDINGS++))
        fi
        
        # Check for JWT tokens (basic pattern)
        if echo "$line" | grep -qE "eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"; then
            echo -e "${RED}⚠️  Found potential JWT token in $file:${NC}"
            echo -e "${YELLOW}   Line $line_num:${NC} ${line:0:100}..."
            ((FINDINGS++))
        fi
        
        # Check for AWS access keys
        if echo "$line" | grep -qE "AKIA[0-9A-Z]{16}"; then
            echo -e "${RED}⚠️  Found potential AWS access key in $file:${NC}"
            echo -e "${YELLOW}   Line $line_num:${NC} ${line:0:100}..."
            ((FINDINGS++))
        fi
        
        # Check for GitHub tokens
        if echo "$line" | grep -qE "ghp_[A-Za-z0-9]{36}"; then
            echo -e "${RED}⚠️  Found potential GitHub token in $file:${NC}"
            echo -e "${YELLOW}   Line $line_num:${NC} ${line:0:100}..."
            ((FINDINGS++))
        fi
        
        # Check for Slack tokens
        if echo "$line" | grep -qE "xox[baprs]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-z0-9]{32}"; then
            echo -e "${RED}⚠️  Found potential Slack token in $file:${NC}"
            echo -e "${YELLOW}   Line $line_num:${NC} ${line:0:100}..."
            ((FINDINGS++))
        fi
        
    done < "$file"
}

# Scan Python files
echo "Scanning Python files..."
echo "-----------------------"
find . -type f -name "*.py" ! -path "*/__pycache__/*" ! -path "*/.git/*" ! -path "*/venv/*" ! -path "*/env/*" | while read -r file; do
    check_secrets "$file"
done

# Scan shell scripts
echo ""
echo "Scanning shell scripts..."
echo "-------------------------"
find . -type f \( -name "*.sh" -o -name "*.bash" \) ! -path "*/.git/*" | while read -r file; do
    check_secrets "$file"
done

# Scan configuration files
echo ""
echo "Scanning configuration files..."
echo "------------------------------"
find . -type f \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.conf" -o -name "*.config" \) ! -path "*/.git/*" ! -path "*/node_modules/*" ! -path "*/venv/*" | while read -r file; do
    check_secrets "$file"
done

# Summary
echo ""
echo "======================"
if [ $FINDINGS -eq 0 ]; then
    echo -e "${GREEN}✅ No secrets found!${NC}"
else
    echo -e "${RED}⚠️  Found $FINDINGS potential secret(s)${NC}"
    echo ""
    echo "Please review the findings above and:"
    echo "1. Remove hardcoded secrets"
    echo "2. Use environment variables instead"
    echo "3. Rotate any exposed credentials"
    echo "4. See SECRET_SCAN_REPORT.md for details"
    exit 1
fi
