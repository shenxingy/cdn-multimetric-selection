#!/usr/bin/env python3
"""
RIPE Atlas CDN Measurement Test Script

Tests connectivity to CDN DNS resolvers using RIPE Atlas probes.
Automatically tries different targets if concurrent measurement limits are hit.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from ripe.atlas.cousteau import (
    Ping,
    AtlasSource,
    AtlasCreateRequest,
    ProbeRequest
)

# Load environment variables
load_dotenv()

# Configuration
PRIMARY_KEY = os.getenv('RIPE_ATLAS_PRIMARY_KEY')
NUM_PROBES = 2           # Number of probes to use (reduced from 5 to save credits)
DURATION_MINUTES = 10     # Measurement duration (reduced from 60 to save credits)
INTERVAL_SECONDS = 300    # Interval between measurements (5 minutes)
DURATION = DURATION_MINUTES * 60  # Convert to seconds
INTERVAL = INTERVAL_SECONDS

# CDN targets to try (in order of preference based on expected availability)
CDN_TARGETS = [
    {'ip': '208.67.222.222', 'name': 'OpenDNS Primary', 'cdn': 'OpenDNS'},
    {'ip': '208.67.220.220', 'name': 'OpenDNS Secondary', 'cdn': 'OpenDNS'},
    {'ip': '9.9.9.9', 'name': 'Quad9 DNS', 'cdn': 'Quad9'},
    {'ip': '1.0.0.1', 'name': 'Cloudflare Secondary', 'cdn': 'Cloudflare'},
    {'ip': '8.8.4.4', 'name': 'Google Secondary DNS', 'cdn': 'Google'},
]

def check_api_key():
    """Verify API key is loaded"""
    if not PRIMARY_KEY:
        print("❌ Error: RIPE_ATLAS_PRIMARY_KEY not found in .env file")
        print("Please check your .env file in the project root")
        return False
    print(f"✓ API key loaded: {PRIMARY_KEY[:10]}...")
    return True

def check_probes():
    """Check available probes"""
    print("\n🔍 Querying RIPE Atlas probe network...")
    try:
        filters = {
            'status': 1,  # Connected probes only
            'tags': 'system-ipv4-works',
        }
        probes = ProbeRequest(**filters)
        probe_list = list(probes)
        print(f"✓ Found {len(probe_list):,} active IPv4-capable probes")
        return True
    except Exception as e:
        print(f"❌ Error querying probes: {e}")
        return False

def create_measurement(target_ip, target_name, cdn_name):
    """
    Create a ping measurement to target IP.
    
    Args:
        target_ip: IP address to ping
        target_name: Descriptive name of target
        cdn_name: CDN provider name
    
    Returns:
        Measurement ID if successful, None otherwise
    """
    print(f"\n🚀 Attempting to create measurement...")
    print(f"   Target: {target_name} ({target_ip})")
    print(f"   Probes: {NUM_PROBES} worldwide")
    print(f"   Duration: {DURATION // 60} minutes")
    print(f"   Interval: {INTERVAL // 60} minutes")
    
    try:
        # Define ping measurement
        ping = Ping(
            af=4,
            target=target_ip,
            description=f"CDN Test - {cdn_name} - {target_name}",
            packets=3
        )
        
        # Define probe source
        source = AtlasSource(
            type="area",
            value="WW",  # Worldwide
            requested=NUM_PROBES,
            tags={"include": ["system-ipv4-works"]}
        )
        
        # Create request
        atlas_request = AtlasCreateRequest(
            key=PRIMARY_KEY,
            measurements=[ping],
            sources=[source],
            is_oneoff=False,
            interval=INTERVAL,
            stop_time=int(time.time()) + DURATION
        )
        
        # Submit
        is_success, response = atlas_request.create()
        
        if is_success:
            measurement_id = response['measurements'][0]
            print(f"\n✅ SUCCESS! Measurement created!")
            print(f"   Measurement ID: {measurement_id}")
            print(f"   View at: https://atlas.ripe.net/measurements/{measurement_id}")
            return measurement_id
        else:
            error_detail = response.get('error', {}).get('errors', [{}])[0].get('detail', str(response))
            print(f"   ❌ Failed: {error_detail}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def save_measurement_metadata(measurement_id, target_info):
    """Save measurement metadata to file"""
    try:
        output_dir = Path('data/raw')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f'ripe_measurement_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        metadata = {
            'created': datetime.now().isoformat(),
            'measurement_id': measurement_id,
            'target': target_info,
            'config': {
                'num_probes': NUM_PROBES,
                'duration_seconds': DURATION,
                'interval_seconds': INTERVAL,
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n💾 Metadata saved to: {output_file}")
        
        # Also save measurement ID to simple text file for easy access
        with open(output_dir / 'latest_measurement_id.txt', 'w') as f:
            f.write(str(measurement_id))
        
        return True
    except Exception as e:
        print(f"⚠️  Warning: Could not save metadata: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("RIPE Atlas CDN Measurement Test")
    print("=" * 60)
    
    # Check API key
    if not check_api_key():
        return
    
    # Check probes
    if not check_probes():
        print("\n⚠️  Warning: Could not verify probes, but continuing anyway...")
    
    # Try each target until one succeeds
    print("\n🎯 Testing CDN targets...")
    for i, target in enumerate(CDN_TARGETS, 1):
        print(f"\n[{i}/{len(CDN_TARGETS)}] Trying {target['name']}...")
        
        measurement_id = create_measurement(
            target['ip'],
            target['name'],
            target['cdn']
        )
        
        if measurement_id:
            # Success! Save metadata and exit
            save_measurement_metadata(measurement_id, target)
            
            print("\n" + "=" * 60)
            print("✅ MEASUREMENT LAUNCHED SUCCESSFULLY!")
            print("=" * 60)
            print(f"\n📊 Next steps:")
            print(f"   1. Wait 10-15 minutes for data to collect")
            print(f"   2. Check progress at: https://atlas.ripe.net/measurements/{measurement_id}")
            print(f"   3. Run data collection script to fetch results")
            print(f"\n💡 Measurement will run for {DURATION // 60} minutes")
            print(f"   ({DURATION // INTERVAL} measurements will be collected)")
            return
        
        # Failed, try next target
        if i < len(CDN_TARGETS):
            print(f"   ⏭️  Trying next target...")
            time.sleep(1)  # Brief delay between attempts
    
    # All targets failed
    print("\n" + "=" * 60)
    print("❌ ALL TARGETS FAILED")
    print("=" * 60)
    print("\n🔍 Possible issues:")
    print("   1. All popular DNS targets have too many concurrent measurements")
    print("   2. API key might lack permissions to create measurements")
    print("   3. RIPE Atlas service might be experiencing issues")
    print("\n💡 Suggestions:")
    print("   1. Try again in a few hours when concurrent measurements decrease")
    print("   2. Verify your API key has 'Schedule new measurement' permission")
    print("   3. Check RIPE Atlas status: https://atlas.ripe.net")

if __name__ == "__main__":
    main()
