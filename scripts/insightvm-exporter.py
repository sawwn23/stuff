#!/usr/bin/env python3
"""
Rapid7 InsightVM Vulnerability Export Tool

Extracts critical & high-severity vulnerabilities per asset from Rapid7 InsightVM Cloud API,
enriches with exploit and solution data, calculates remediation time, and exports to CSV.

🎯 Perfect for vulnerability management with comprehensive Excel/Power BI ready output!
"""

import requests
import pandas as pd
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import time

# ─── CONFIGURATION ──────────────────────────────────────────────────────────────

CONFIG = {
    'api_key': "YOUR_API_KEY",  # Replace with your actual API key
    'base_url': "https://us.api.insight.rapid7.com/vm/v4",  # Change region if needed
    'max_assets': 100,                  # Number of assets to process (for testing use 10–50)
    'include_exploit': True,           # Include exploit title if found
    'include_solution': True,          # Include solution summary
    'calculate_remediation_time': True, # Add fix time in days
    'output_csv': "vuln_export.csv"    # Output file name
}

class Rapid7VulnExporter:
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the exporter with configuration."""
        self.config = config or CONFIG
        self._validate_config()
        self.session = self._setup_session()
        self.vulnerabilities = []
        
    def _validate_config(self):
        """Validate configuration settings."""
        if not self.config.get('api_key') or self.config['api_key'] == "YOUR_API_KEY":
            print("❌ Please set your API key in the CONFIG dictionary")
            print("   Edit the CONFIG['api_key'] value in this script")
            sys.exit(1)
    
    def _setup_session(self) -> requests.Session:
        """Setup HTTP session with authentication."""
        session = requests.Session()
        session.headers.update({
            'X-Api-Key': self.config['api_key'],
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        return session
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated API request with error handling."""
        url = f"{self.config['base_url']}{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                print("❌ Authentication failed. Check your API key.")
            elif response.status_code == 403:
                print("❌ Access forbidden. Check your permissions.")
            elif response.status_code == 404:
                print(f"❌ Endpoint not found: {endpoint}")
            else:
                print(f"❌ HTTP Error {response.status_code}: {e}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            sys.exit(1)
    
    def get_assets(self) -> List[Dict]:
        """Fetch assets from the API."""
        print("🔍 Fetching assets...")
        
        assets = []
        page = 0
        size = min(500, self.config['max_assets'])  # API max page size is 500
        
        while len(assets) < self.config['max_assets']:
            params = {
                'page': page,
                'size': min(size, self.config['max_assets'] - len(assets))
            }
            
            response = self._make_request('/assets', params)
            
            if not response.get('data'):
                break
                
            batch_assets = response['data']
            assets.extend(batch_assets)
            
            print(f"   Retrieved {len(batch_assets)} assets (total: {len(assets)})")
            
            # Check if we have more pages
            if len(batch_assets) < size or len(assets) >= self.config['max_assets']:
                break
                
            page += 1
            time.sleep(0.1)  # Rate limiting
        
        print(f"✅ Retrieved {len(assets)} assets")
        return assets[:self.config['max_assets']]
    
    def get_asset_vulnerabilities(self, asset_id: str) -> List[Dict]:
        """Fetch critical and high vulnerabilities for a specific asset."""
        endpoint = f"/assets/{asset_id}/vulnerabilities"
        params = {
            'severity': 'CRITICAL,HIGH',
            'size': 500  # Max page size
        }
        
        vulnerabilities = []
        page = 0
        
        while True:
            params['page'] = page
            response = self._make_request(endpoint, params)
            
            if not response.get('data'):
                break
                
            batch_vulns = response['data']
            vulnerabilities.extend(batch_vulns)
            
            # Check if we have more pages
            if len(batch_vulns) < 500:
                break
                
            page += 1
            time.sleep(0.05)  # Rate limiting
        
        return vulnerabilities
    
    def get_vulnerability_solutions(self, vuln_id: str) -> Optional[str]:
        """Get solution summary for a vulnerability."""
        if not self.config.get('include_solution'):
            return None
            
        try:
            endpoint = f"/vulnerabilities/{vuln_id}/solutions"
            response = self._make_request(endpoint)
            
            solutions = response.get('data', [])
            if solutions:
                # Get the first solution summary
                return solutions[0].get('summary', '')
        except:
            # If solution fetch fails, continue without it
            pass
        
        return None
    
    def get_vulnerability_exploits(self, vuln_id: str) -> Optional[str]:
        """Get exploit information for a vulnerability."""
        if not self.config.get('include_exploit'):
            return None
            
        try:
            endpoint = f"/vulnerabilities/{vuln_id}/exploits"
            response = self._make_request(endpoint)
            
            exploits = response.get('data', [])
            if exploits:
                # Get the first exploit title
                return exploits[0].get('title', '')
        except:
            # If exploit fetch fails, continue without it
            pass
        
        return None
    
    def calculate_remediation_days(self, first_discovered: str, fixed_at: str) -> Optional[int]:
        """Calculate remediation time in days."""
        if not self.config.get('calculate_remediation_time') or not fixed_at:
            return None
            
        try:
            first_date = datetime.fromisoformat(first_discovered.replace('Z', '+00:00'))
            fixed_date = datetime.fromisoformat(fixed_at.replace('Z', '+00:00'))
            return (fixed_date - first_date).days
        except:
            return None
    
    def calculate_vulnerability_age(self, first_discovered: str) -> Optional[int]:
        """Calculate how many days since vulnerability was first discovered."""
        if not first_discovered:
            return None
            
        try:
            first_date = datetime.fromisoformat(first_discovered.replace('Z', '+00:00'))
            current_date = datetime.now(first_date.tzinfo)
            return (current_date - first_date).days
        except:
            return None
    
    def determine_asset_criticality(self, tags: str) -> str:
        """Determine asset criticality based on tags."""
        tags_lower = tags.lower()
        
        if any(keyword in tags_lower for keyword in ['critical', 'prod', 'production', 'dmz']):
            return 'Critical'
        elif any(keyword in tags_lower for keyword in ['high', 'important', 'server']):
            return 'High'
        elif any(keyword in tags_lower for keyword in ['medium', 'staging', 'test']):
            return 'Medium'
        elif any(keyword in tags_lower for keyword in ['low', 'dev', 'development']):
            return 'Low'
        else:
            return 'Unknown'
    
    def process_assets(self):
        """Process all assets and extract vulnerability data."""
        assets = self.get_assets()
        
        print(f"🔍 Processing vulnerabilities for {len(assets)} assets...")
        
        for i, asset in enumerate(assets, 1):
            asset_id = asset.get('id')
            hostname = asset.get('hostName', 'Unknown')
            ip_address = asset.get('ipAddress', 'Unknown')
            os_info = asset.get('operatingSystem', {}).get('description', 'Unknown')
            tags = ', '.join([tag.get('name', '') for tag in asset.get('tags', [])])
            
            print(f"   [{i}/{len(assets)}] Processing {hostname} ({ip_address})")
            
            # Get vulnerabilities for this asset
            vulnerabilities = self.get_asset_vulnerabilities(asset_id)
            
            for vuln in vulnerabilities:
                vuln_id = vuln.get('id')
                cve = vuln.get('cve', vuln_id)  # Use vuln ID if no CVE
                title = vuln.get('title', 'Unknown')
                severity = vuln.get('severity', 'Unknown')
                cvss = vuln.get('cvssScore')
                first_discovered = vuln.get('firstDiscovered')
                fixed_at = vuln.get('fixedAt')
                
                # Get enrichment data
                solution = self.get_vulnerability_solutions(vuln_id)
                exploit = self.get_vulnerability_exploits(vuln_id)
                remediation_days = self.calculate_remediation_days(first_discovered, fixed_at)
                
                # Calculate additional vulnerability management fields
                vuln_age_days = self.calculate_vulnerability_age(first_discovered)
                status = vuln.get('status', 'Open')
                risk_score = vuln.get('riskScore', 0)
                categories = ', '.join(vuln.get('categories', []))
                patch_available = 'Yes' if solution else 'No'
                
                # Determine asset criticality from tags
                asset_criticality = self.determine_asset_criticality(tags)
                
                # Add to results
                self.vulnerabilities.append({
                    'Hostname': hostname,
                    'IP': ip_address,
                    'OS': os_info,
                    'Tags': tags,
                    'Asset Criticality': asset_criticality,
                    'CVE': cve,
                    'Title': title,
                    'Severity': severity,
                    'CVSS': cvss,
                    'Risk Score': risk_score,
                    'Status': status,
                    'Categories': categories,
                    'First Discovered': first_discovered,
                    'Vulnerability Age (Days)': vuln_age_days,
                    'Fixed At': fixed_at,
                    'Remediation Days': remediation_days,
                    'Patch Available': patch_available,
                    'Exploit Available': 'Yes' if exploit else 'No',
                    'Exploit Title': exploit,
                    'Solution': solution
                })
            
            # Rate limiting
            time.sleep(0.1)
        
        print(f"✅ Processed {len(self.vulnerabilities)} vulnerabilities")
    
    def export_to_csv(self):
        """Export vulnerability data to CSV file."""
        if not self.vulnerabilities:
            print("❌ No vulnerabilities to export")
            return
        
        print(f"📤 Exporting to {self.config['output_csv']}...")
        
        # Create DataFrame
        df = pd.DataFrame(self.vulnerabilities)
        
        # Sort by severity (Critical first) and CVSS score
        severity_order = {'CRITICAL': 0, 'HIGH': 1}
        df['severity_rank'] = df['Severity'].map(severity_order)
        df = df.sort_values(['severity_rank', 'CVSS'], ascending=[True, False])
        df = df.drop('severity_rank', axis=1)
        
        # Export to CSV
        df.to_csv(self.config['output_csv'], index=False)
        
        print(f"✅ Exported {len(df)} vulnerabilities to {self.config['output_csv']}")
        
        # Print summary statistics
        print("\n📊 Vulnerability Management Summary:")
        print(f"   Total vulnerabilities: {len(df)}")
        print(f"   Critical: {len(df[df['Severity'] == 'CRITICAL'])}")
        print(f"   High: {len(df[df['Severity'] == 'HIGH'])}")
        print(f"   Unique assets: {df['Hostname'].nunique()}")
        
        # Status breakdown
        status_counts = df['Status'].value_counts()
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
        
        # Asset criticality breakdown
        criticality_counts = df['Asset Criticality'].value_counts()
        print(f"\n   Asset Criticality:")
        for criticality, count in criticality_counts.items():
            print(f"     {criticality}: {count}")
        
        # Exploit availability
        exploits_available = len(df[df['Exploit Available'] == 'Yes'])
        print(f"\n   Exploits available: {exploits_available}")
        print(f"   Patches available: {len(df[df['Patch Available'] == 'Yes'])}")
        
        # Age statistics
        if 'Vulnerability Age (Days)' in df.columns:
            avg_age = df['Vulnerability Age (Days)'].mean()
            print(f"   Average vulnerability age: {avg_age:.1f} days")
        
        if self.config.get('calculate_remediation_time'):
            fixed_vulns = df[df['Remediation Days'].notna()]
            if not fixed_vulns.empty:
                avg_remediation = fixed_vulns['Remediation Days'].mean()
                print(f"   Average remediation time: {avg_remediation:.1f} days")
    
    def run(self):
        """Main execution method."""
        print("🚀 Starting Rapid7 InsightVM Vulnerability Export")
        print(f"   Base URL: {self.config['base_url']}")
        print(f"   Max assets: {self.config['max_assets']}")
        print(f"   Include exploits: {self.config['include_exploit']}")
        print(f"   Include solutions: {self.config['include_solution']}")
        print(f"   Calculate remediation time: {self.config['calculate_remediation_time']}")
        print()
        
        try:
            self.process_assets()
            self.export_to_csv()
            print("\n🎉 Export completed successfully!")
        except KeyboardInterrupt:
            print("\n⚠️  Export interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Export failed: {e}")
            sys.exit(1)

def main():
    """Main entry point."""
    print("=" * 60)
    print("🎯 RAPID7 INSIGHTVM VULNERABILITY MANAGEMENT EXPORT")
    print("   Extract, enrich, and export vulnerabilities to Excel/Power BI")
    print("=" * 60)
    print()
    
    # You can override config here if needed
    # custom_config = CONFIG.copy()
    # custom_config['max_assets'] = 50
    # exporter = Rapid7VulnExporter(custom_config)
    
    exporter = Rapid7VulnExporter()
    exporter.run()

if __name__ == "__main__":
    main()