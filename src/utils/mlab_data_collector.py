#!/usr/bin/env python3
"""
M-Lab Data Collector
Collects real CDN/network performance measurements from M-Lab's BigQuery dataset

Requirements:
- Google Cloud project with BigQuery API enabled
- M-Lab Discuss group membership (for free queries)
- Billing enabled on your project
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from google.cloud import bigquery
import pandas as pd

# Project configuration
PROJECT_ID = 'cdn-adv-comp-network-project'
MLAB_PROJECT = 'measurement-lab'

# Output configuration
OUTPUT_DIR = Path('data/raw')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_bigquery_client():
    """Initialize BigQuery client"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        print(f"✓ Connected to BigQuery project: {PROJECT_ID}")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to BigQuery: {e}")
        sys.exit(1)


def collect_ndt_sample(client, days_back=30, sample_size=50000, country_code='US'):
    """
    Collect sample of NDT (Network Diagnostic Tool) measurements
    
    NDT measures:
    - Download/upload throughput
    - Round-trip time (RTT)
    - Packet retransmission rates
    - Network path characteristics
    
    Args:
        client: BigQuery client
        days_back: Number of days to look back
        sample_size: Number of records to collect
        country_code: ISO country code (e.g., 'US', 'GB')
    """
    print(f"\n{'='*60}")
    print("Collecting M-Lab NDT Measurements")
    print(f"{'='*60}")
    print(f"📊 Parameters:")
    print(f"   - Time range: Last {days_back} days")
    print(f"   - Sample size: {sample_size:,} records")
    print(f"   - Country filter: {country_code}")
    print(f"   - Dataset: {MLAB_PROJECT}.ndt.unified_downloads")
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    # Query for NDT download measurements with key CDN metrics
    query = f"""
    SELECT
        -- Timestamp and location
        date,
        
        -- Client location
        Client.Geo.Latitude as client_lat,
        Client.Geo.Longitude as client_lon,
        Client.Geo.City as client_city,
        Client.Geo.CountryCode as client_country,
        Client.Network.ASNumber as client_asn,
        Client.Network.ASName as client_isp,
        
        -- Server information
        Server.Geo.Latitude as server_lat,
        Server.Geo.Longitude as server_lon,
        Server.Site as server_site,
        Server.Geo.City as server_city,
        
        -- Network performance metrics
        a.MeanThroughputMbps as download_mbps,
        a.MinRTT as min_rtt_ms,
        a.LossRate as packet_loss_rate
        
    FROM 
        `{MLAB_PROJECT}.ndt.unified_downloads`
    WHERE
        date >= '{start_date.strftime('%Y-%m-%d')}'
        AND date <= '{end_date.strftime('%Y-%m-%d')}'
        AND Client.Geo.CountryCode = '{country_code}'
        AND a.MeanThroughputMbps IS NOT NULL
        AND a.MinRTT IS NOT NULL
        AND a.MeanThroughputMbps > 0
        AND a.MinRTT > 0
        AND Client.Geo.Latitude IS NOT NULL
        AND Server.Geo.Latitude IS NOT NULL
    LIMIT {sample_size}
    """
    
    print(f"\n🔍 Executing query...")
    print(f"   (This may take 30-60 seconds for {sample_size:,} records)")
    
    try:
        # Execute query
        query_job = client.query(query)
        
        # Get results as dataframe
        df = query_job.to_dataframe()
        
        print(f"\n✓ Query completed successfully!")
        print(f"   Records retrieved: {len(df):,}")
        print(f"   Estimated bytes processed: {query_job.total_bytes_processed:,}")
        print(f"   Query cost: $0 (M-Lab Discuss member)")
        
        # Display sample statistics
        print(f"\n📈 Data Summary:")
        print(f"   Download speed: {df['download_mbps'].mean():.2f} Mbps (mean)")
        print(f"   RTT: {df['min_rtt_ms'].mean():.2f} ms (mean)")
        if 'packet_loss_rate' in df.columns and df['packet_loss_rate'].notna().any():
            print(f"   Packet loss: {df['packet_loss_rate'].mean()*100:.3f}% (mean)")
        print(f"   Unique cities: {df['client_city'].nunique()}")
        print(f"   Unique servers: {df['server_site'].nunique()}")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        
        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = OUTPUT_DIR / f'mlab_ndt_{country_code.lower()}_{days_back}days_{timestamp}.csv'
        df.to_csv(output_file, index=False)
        print(f"\n💾 Data saved to: {output_file}")
        
        return df, output_file
        
    except Exception as e:
        print(f"\n❌ Query failed: {e}")
        return None, None


def analyze_cdn_distribution(df):
    """Analyze CDN/server distribution in the dataset"""
    if df is None or df.empty:
        return
    
    print(f"\n{'='*60}")
    print("CDN/Server Distribution Analysis")
    print(f"{'='*60}")
    
    # Top servers by measurement count
    print("\n🌐 Top 10 Servers (by measurement count):")
    top_servers = df['server_site'].value_counts().head(10)
    for i, (server, count) in enumerate(top_servers.items(), 1):
        pct = (count / len(df)) * 100
        print(f"   {i:2d}. {server:30s} - {count:,} measurements ({pct:.1f}%)")
    
    # Geographic distribution
    print(f"\n🗺️  Top 10 Client Cities:")
    top_locations = df['client_city'].value_counts().head(10)
    for i, (loc, count) in enumerate(top_locations.items(), 1):
        pct = (count / len(df)) * 100
        print(f"   {i:2d}. {loc:20s} - {count:,} measurements ({pct:.1f}%)")
    
    # Performance by location
    print(f"\n⚡ Average Performance by Top 5 Cities:")
    top_5_locs = df['client_city'].value_counts().head(5).index
    for loc in top_5_locs:
        loc_data = df[df['client_city'] == loc]
        avg_speed = loc_data['download_mbps'].mean()
        avg_rtt = loc_data['min_rtt_ms'].mean()
        print(f"   {loc:20s} - {avg_speed:6.1f} Mbps, {avg_rtt:5.1f} ms RTT")


def main():
    """Main execution"""
    print(f"\n{'='*60}")
    print("M-Lab Data Collection Tool")
    print(f"{'='*60}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize client
    client = get_bigquery_client()
    
    # Collect NDT data
    df, output_file = collect_ndt_sample(
        client,
        days_back=30,
        sample_size=50000,
        country_code='US'
    )
    
    if df is not None:
        # Analyze the data
        analyze_cdn_distribution(df)
        
        print(f"\n{'='*60}")
        print("✅ Collection Complete!")
        print(f"{'='*60}")
        print(f"Output file: {output_file}")
        print(f"Records: {len(df):,}")
        print(f"Ready for analysis in notebooks/")
    else:
        print("\n❌ Collection failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
