#!/usr/bin/env python3
"""
Rapid7 InsightVM Vulnerability Export Tool

Extracts critical & high-severity vulnerabilities per asset from Rapid7 InsightVM Cloud API,
enriches with exploit and solution data, calculates remediation time, and exports to CSV.

vulnerability management with comprehensive Excel/Power BI ready output!
"""

import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import time

# ─── CONFIGURATION ──────────────────────────────────────────────────────────────

CONFIG = {
    # Cloud API (v4) Configuration
    'api_key': "YOUR_API_KEY",  # Replace with your actual API key
    'base_url': "https://us.api.insight.rapid7.com/vm/v4",  # Change region if needed
    
    # On-premise API (v3) Configuration for detailed vulnerability data
    'v3_enabled': False,               # Enable v3 API for detailed vulnerability data
    'v3_console_url': "https://your-console:3780",  # Your InsightVM console URL
    'v3_username': "your_username",    # Console username
    'v3_password': "your_password",    # Console password
    
    # General Configuration
    'max_assets': 100,                  # Number of assets to process (for testing use 10–50)
    'include_exploit': True,           # Include exploit title if found
    'include_solution': True,          # Include solution summary
    'calculate_remediation_time': True, # Add fix time in days
    'output_csv': None                 # Will be auto-generated with date
}

class Rapid7VulnExporter:
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the exporter with configuration."""
        self.config = config or CONFIG
        self._validate_config()
        self._set_output_filename()
        self.session = self._setup_session()
        self.v3_session = self._setup_v3_session() if self.config.get('v3_enabled') else None
        self.vulnerabilities = []
        
    def _validate_config(self):
        """Validate configuration settings."""
        if not self.config.get('api_key') or self.config['api_key'] == "YOUR_API_KEY":
            print("ERROR: Please set your API key in the CONFIG dictionary")
            print("   Edit the CONFIG['api_key'] value in this script")
            sys.exit(1)
    
    def _set_output_filename(self):
        """Set output filename with current date if not specified."""
        if not self.config.get('output_csv'):
            current_date = datetime.now().strftime("%y-%m-%d")
            self.config['output_csv'] = f"export-{current_date}.csv"
    
    def _setup_session(self) -> requests.Session:
        """Setup HTTP session with authentication for v4 Cloud API."""
        session = requests.Session()
        session.headers.update({
            'X-Api-Key': self.config['api_key'],
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        return session
    
    def _setup_v3_session(self) -> requests.Session:
        """Setup HTTP session with Basic Auth for v3 On-premise API."""
        session = requests.Session()
        session.auth = HTTPBasicAuth(self.config['v3_username'], self.config['v3_password'])
        session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        return session
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated GET API request with error handling."""
        url = f"{self.config['base_url']}{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                print("ERROR: Authentication failed. Check your API key.")
            elif response.status_code == 403:
                print("ERROR: Access forbidden. Check your permissions.")
            elif response.status_code == 404:
                print(f"ERROR: Endpoint not found: {endpoint}")
            else:
                print(f"ERROR: HTTP Error {response.status_code}: {e}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Request failed: {e}")
            sys.exit(1)
    
    def _make_request_post(self, endpoint: str, params: Dict = None, body: Dict = None) -> Dict:
        """Make authenticated POST API request with error handling."""
        url = f"{self.config['base_url']}{endpoint}"
        
        try:
            response = self.session.post(url, params=params, json=body)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                print("ERROR: Authentication failed. Check your API key.")
            elif response.status_code == 403:
                print("ERROR: Access forbidden. Check your permissions.")
            elif response.status_code == 404:
                print(f"ERROR: Endpoint not found: {endpoint}")
            else:
                print(f"ERROR: HTTP Error {response.status_code}: {e}")
                print(f"Response: {response.text}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Request failed: {e}")
            sys.exit(1)
    
    def get_assets(self) -> List[Dict]:
        """Fetch assets from the API using the correct integration endpoint."""
        print("INFO: Fetching assets with vulnerabilities...")
        
        assets = []
        page = 0
        size = min(500, self.config['max_assets'])  # API max page size is 500
        
        while len(assets) < self.config['max_assets']:
            # Prepare the search query for critical and high vulnerabilities
            search_body = {
                "vulnerability": "severity IN ['Critical', 'Severe']"  # Critical = Critical, Severe = High
            }
            
            params = {
                'page': page,
                'size': min(size, self.config['max_assets'] - len(assets))
            }
            
            response = self._make_request_post('/integration/assets', params, search_body)
            
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
        
        print(f"SUCCESS: Retrieved {len(assets)} assets with vulnerabilities")
        return assets[:self.config['max_assets']]
    
    def extract_vulnerabilities_from_asset(self, asset: Dict) -> List[Dict]:
        """Extract vulnerability information from asset data."""
        vulnerabilities = []
        
        # Get basic asset info
        hostname = asset.get('host_name', 'Unknown')
        ip_address = asset.get('ip', 'Unknown')
        os_info = asset.get('os_description', 'Unknown')
        tags = ', '.join([tag.get('name', '') for tag in asset.get('tags', [])])
        asset_criticality = self.determine_asset_criticality(tags)
        asset_id = asset.get('id')
        
        # Get vulnerability counts from asset summary
        critical_count = asset.get('critical_vulnerabilities', 0)
        severe_count = asset.get('severe_vulnerabilities', 0)  # This is "High" in InsightVM
        risk_score = asset.get('risk_score', 0)
        
        # If v3 API is enabled, get detailed vulnerability data
        if self.config.get('v3_enabled') and asset_id:
            v3_vulnerabilities = self.get_v3_asset_vulnerabilities(asset_id)
            
            for v3_vuln in v3_vulnerabilities:
                # Get additional details for each vulnerability
                vuln_id = v3_vuln.get('id')
                vuln_details = self.get_v3_vulnerability_details(vuln_id)
                
                vuln_data = self.create_v3_vulnerability_record(
                    hostname, ip_address, os_info, tags, asset_criticality,
                    v3_vuln, vuln_details, risk_score
                )
                vulnerabilities.append(vuln_data)
            
            return vulnerabilities
        
        # Fallback to v4 API data processing
        # Process new vulnerabilities (recently discovered)
        new_vulns = asset.get('new', [])
        for vuln in new_vulns:
            vuln_data = self.create_vulnerability_record(
                hostname, ip_address, os_info, tags, asset_criticality,
                vuln, 'New', risk_score
            )
            vulnerabilities.append(vuln_data)
        
        # Process remediated vulnerabilities (recently fixed)
        remediated_vulns = asset.get('remediated', [])
        for vuln in remediated_vulns:
            vuln_data = self.create_vulnerability_record(
                hostname, ip_address, os_info, tags, asset_criticality,
                vuln, 'Remediated', risk_score
            )
            vulnerabilities.append(vuln_data)
        
        # If no specific vulnerability details but we have counts, create summary records
        if not vulnerabilities and (critical_count > 0 or severe_count > 0):
            if critical_count > 0:
                summary_vuln = self.create_summary_vulnerability_record(
                    hostname, ip_address, os_info, tags, asset_criticality,
                    'Critical', critical_count, risk_score
                )
                vulnerabilities.append(summary_vuln)
            
            if severe_count > 0:
                summary_vuln = self.create_summary_vulnerability_record(
                    hostname, ip_address, os_info, tags, asset_criticality,
                    'High', severe_count, risk_score
                )
                vulnerabilities.append(summary_vuln)
        
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
    
    def _make_v3_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated GET API request to v3 on-premise API."""
        if not self.v3_session:
            return {}
            
        url = f"{self.config['v3_console_url']}/api/3{endpoint}"
        
        try:
            response = self.v3_session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"WARNING: v3 API request failed for {endpoint}: {e}")
            return {}
        except requests.exceptions.RequestException as e:
            print(f"WARNING: v3 API request failed for {endpoint}: {e}")
            return {}
    
    def get_v3_asset_vulnerabilities(self, asset_id: str) -> List[Dict]:
        """Get detailed vulnerability data from v3 API for an asset."""
        if not self.config.get('v3_enabled'):
            return []
            
        print(f"      Fetching detailed vulnerabilities from v3 API...")
        
        vulnerabilities = []
        page = 0
        size = 500
        
        while True:
            params = {
                'page': page,
                'size': size
            }
            
            response = self._make_v3_request(f'/assets/{asset_id}/vulnerabilities', params)
            
            if not response.get('resources'):
                break
                
            batch_vulns = response['resources']
            vulnerabilities.extend(batch_vulns)
            
            # Check if we have more pages
            if len(batch_vulns) < size:
                break
                
            page += 1
            time.sleep(0.05)  # Rate limiting
        
        return vulnerabilities
    
    def get_v3_vulnerability_details(self, vuln_id: str) -> Dict:
        """Get detailed vulnerability information from v3 API."""
        if not self.config.get('v3_enabled'):
            return {}
            
        return self._make_v3_request(f'/vulnerabilities/{vuln_id}')
    
    def get_v3_vulnerability_solutions(self, vuln_id: str) -> List[Dict]:
        """Get vulnerability solutions from v3 API."""
        if not self.config.get('v3_enabled'):
            return []
            
        response = self._make_v3_request(f'/vulnerabilities/{vuln_id}/solutions')
        return response.get('resources', [])
    
    def create_vulnerability_record(self, hostname: str, ip_address: str, os_info: str, 
                                  tags: str, asset_criticality: str, vuln: Dict, 
                                  status: str, risk_score: float) -> Dict:
        """Create a vulnerability record from asset vulnerability data."""
        vuln_id = vuln.get('id', 'Unknown')
        cve = vuln.get('cve', vuln_id)
        title = vuln.get('title', 'Unknown')
        severity = vuln.get('severity', 'Unknown')
        cvss = vuln.get('cvss_score', 0)
        first_discovered = vuln.get('first_discovered')
        fixed_at = vuln.get('fixed_at') if status == 'Remediated' else None
        
        # Calculate additional fields
        vuln_age_days = self.calculate_vulnerability_age(first_discovered)
        remediation_days = self.calculate_remediation_days(first_discovered, fixed_at)
        
        # Get enrichment data if enabled
        solution = self.get_vulnerability_solutions(vuln_id) if self.config.get('include_solution') else None
        exploit = self.get_vulnerability_exploits(vuln_id) if self.config.get('include_exploit') else None
        
        return {
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
            'Categories': vuln.get('categories', ''),
            'First Discovered': first_discovered,
            'Vulnerability Age (Days)': vuln_age_days,
            'Fixed At': fixed_at,
            'Remediation Days': remediation_days,
            'Patch Available': 'Yes' if solution else 'No',
            'Exploit Available': 'Yes' if exploit else 'No',
            'Exploit Title': exploit,
            'Solution': solution
        }
    
    def create_summary_vulnerability_record(self, hostname: str, ip_address: str, os_info: str,
                                          tags: str, asset_criticality: str, severity: str,
                                          count: int, risk_score: float) -> Dict:
        """Create a summary vulnerability record when detailed data isn't available."""
        return {
            'Hostname': hostname,
            'IP': ip_address,
            'OS': os_info,
            'Tags': tags,
            'Asset Criticality': asset_criticality,
            'CVE': f'SUMMARY-{severity}',
            'Title': f'{count} {severity} vulnerabilities found',
            'Severity': severity,
            'CVSS': 0,
            'Risk Score': risk_score,
            'Status': 'Open',
            'Categories': 'Summary',
            'First Discovered': None,
            'Vulnerability Age (Days)': None,
            'Fixed At': None,
            'Remediation Days': None,
            'Patch Available': 'Unknown',
            'Exploit Available': 'Unknown',
            'Exploit Title': None,
            'Solution': f'Review and remediate {count} {severity.lower()} vulnerabilities on this asset'
        }
    
    def create_v3_vulnerability_record(self, hostname: str, ip_address: str, os_info: str,
                                     tags: str, asset_criticality: str, v3_vuln: Dict,
                                     vuln_details: Dict, risk_score: float) -> Dict:
        """Create a vulnerability record from v3 API data with enhanced details."""
        vuln_id = v3_vuln.get('id', 'Unknown')
        
        # Get basic vulnerability info
        status = v3_vuln.get('status', 'Open')
        first_discovered = v3_vuln.get('first', {}).get('date')
        last_seen = v3_vuln.get('most_recently', {}).get('date')
        
        # Get detailed vulnerability info from vuln_details
        cve = vuln_details.get('cve', vuln_id)
        title = vuln_details.get('title', 'Unknown')
        severity = vuln_details.get('severity', 'Unknown')
        cvss_score = vuln_details.get('cvss', {}).get('v2', {}).get('score', 0)
        categories = ', '.join(vuln_details.get('categories', []))
        description = vuln_details.get('description', {}).get('text', '')
        
        # Calculate additional fields
        vuln_age_days = self.calculate_vulnerability_age(first_discovered)
        remediation_days = None
        if status.lower() in ['fixed', 'remediated']:
            remediation_days = self.calculate_remediation_days(first_discovered, last_seen)
        
        # Get solutions from v3 API if enabled
        solutions = []
        if self.config.get('include_solution'):
            solutions = self.get_v3_vulnerability_solutions(vuln_id)
        
        solution_text = ''
        if solutions:
            solution_text = solutions[0].get('summary', '') if solutions else ''
        
        # Check for exploits (simplified - v3 API has different structure)
        exploit_available = 'Unknown'
        exploit_title = None
        
        return {
            'Hostname': hostname,
            'IP': ip_address,
            'OS': os_info,
            'Tags': tags,
            'Asset Criticality': asset_criticality,
            'CVE': cve,
            'Title': title,
            'Severity': severity,
            'CVSS': cvss_score,
            'Risk Score': risk_score,
            'Status': status,
            'Categories': categories,
            'First Discovered': first_discovered,
            'Vulnerability Age (Days)': vuln_age_days,
            'Fixed At': last_seen if status.lower() in ['fixed', 'remediated'] else None,
            'Remediation Days': remediation_days,
            'Patch Available': 'Yes' if solution_text else 'No',
            'Exploit Available': exploit_available,
            'Exploit Title': exploit_title,
            'Solution': solution_text,
            'Description': description[:200] + '...' if len(description) > 200 else description
        }
    
    def process_assets(self):
        """Process all assets and extract vulnerability data."""
        assets = self.get_assets()
        
        print(f"INFO: Processing vulnerabilities for {len(assets)} assets...")
        
        for i, asset in enumerate(assets, 1):
            hostname = asset.get('host_name', 'Unknown')
            ip_address = asset.get('ip', 'Unknown')
            
            print(f"   [{i}/{len(assets)}] Processing {hostname} ({ip_address})")
            
            # Extract vulnerabilities from this asset
            asset_vulnerabilities = self.extract_vulnerabilities_from_asset(asset)
            self.vulnerabilities.extend(asset_vulnerabilities)
            
            # Rate limiting
            time.sleep(0.1)
        
        print(f"SUCCESS: Processed {len(self.vulnerabilities)} vulnerability records")
    
    def export_to_csv(self):
        """Export vulnerability data to CSV file."""
        if not self.vulnerabilities:
            print("WARNING: No vulnerabilities to export")
            return
        
        print(f"INFO: Exporting to {self.config['output_csv']}...")
        
        # Create DataFrame
        df = pd.DataFrame(self.vulnerabilities)
        
        # Sort by severity (Critical first) and CVSS score
        severity_order = {'CRITICAL': 0, 'HIGH': 1}
        df['severity_rank'] = df['Severity'].map(severity_order)
        df = df.sort_values(['severity_rank', 'CVSS'], ascending=[True, False])
        df = df.drop('severity_rank', axis=1)
        
        # Export to CSV
        df.to_csv(self.config['output_csv'], index=False)
        
        print(f"SUCCESS: Exported {len(df)} vulnerabilities to {self.config['output_csv']}")
        
        # Print summary statistics
        print("\nVulnerability Management Summary:")
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
        print("Starting Rapid7 InsightVM Vulnerability Export")
        print(f"   Cloud API (v4): {self.config['base_url']}")
        print(f"   Max assets: {self.config['max_assets']}")
        
        if self.config.get('v3_enabled'):
            print(f"   On-premise API (v3): {self.config['v3_console_url']}/api/3")
            print("   Hybrid mode: Using v4 for assets + v3 for detailed vulnerabilities")
        else:
            print("   Cloud-only mode: Using v4 API only")
            
        print(f"   Include exploits: {self.config['include_exploit']}")
        print(f"   Include solutions: {self.config['include_solution']}")
        print(f"   Calculate remediation time: {self.config['calculate_remediation_time']}")
        print()
        
        try:
            self.process_assets()
            self.export_to_csv()
            print("\nSUCCESS: Export completed successfully!")
        except KeyboardInterrupt:
            print("\nWARNING: Export interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\nERROR: Export failed: {e}")
            sys.exit(1)

def main():
    """Main entry point."""
    print("=" * 60)
    print("RAPID7 INSIGHTVM VULNERABILITY MANAGEMENT EXPORT")
    print("Extract, enrich, and export vulnerabilities to Excel/Power BI")
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