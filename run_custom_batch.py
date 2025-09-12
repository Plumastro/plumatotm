#!/usr/bin/env python3
"""
Easy-to-use script for running custom batch processing
Just paste your profiles and run!
"""

from custom_batch_processor import CustomBatchProcessor

def main():
    """Main function - just paste your profiles here and run!"""
    
    # =============================================================================
    # PASTE YOUR PROFILES HERE - Replace this section with your actual data
    # =============================================================================
    
    profiles_input = '''
{
  "name": "",
  "date": "1962-03-14",
  "time": "07:33",
  "lat": 40.4168,
  "lon": -3.7038,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1995-11-21",
  "time": "18:02",
  "lat": 35.6895,
  "lon": 139.6917,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2017-06-08",
  "time": "01:19",
  "lat": -33.8688,
  "lon": 151.2093,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1944-01-29",
  "time": "22:40",
  "lat": 55.7558,
  "lon": 37.6173,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1971-05-25",
  "time": "13:57",
  "lat": -23.5505,
  "lon": -46.6333,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1990-09-18",
  "time": "04:12",
  "lat": 19.4326,
  "lon": -99.1332,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2009-12-30",
  "time": "15:23",
  "lat": 34.0522,
  "lon": -118.2437,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1938-07-16",
  "time": "09:44",
  "lat": 41.9028,
  "lon": 12.4964,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1966-02-04",
  "time": "20:59",
  "lat": 48.8566,
  "lon": 2.3522,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1985-04-27",
  "time": "06:31",
  "lat": -1.2921,
  "lon": 36.8219,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2013-08-15",
  "time": "11:08",
  "lat": -26.2041,
  "lon": 28.0473,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1958-10-23",
  "time": "02:54",
  "lat": 31.2304,
  "lon": 121.4737,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1998-01-19",
  "time": "21:47",
  "lat": -34.6037,
  "lon": -58.3816,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2016-05-03",
  "time": "17:39",
  "lat": 52.5200,
  "lon": 13.4050,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1949-11-06",
  "time": "05:22",
  "lat": 43.6532,
  "lon": -79.3832,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1974-09-12",
  "time": "14:01",
  "lat": 13.7563,
  "lon": 100.5018,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2001-03-04",
  "time": "09:14",
  "lat": 25.2769,
  "lon": 55.2962,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1931-12-28",
  "time": "19:37",
  "lat": 59.9139,
  "lon": 10.7522,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1969-06-17",
  "time": "08:25",
  "lat": 30.0444,
  "lon": 31.2357,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1981-03-10",
  "time": "00:53",
  "lat": 39.9042,
  "lon": 116.4074,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2018-02-14",
  "time": "12:18",
  "lat": -36.8485,
  "lon": 174.7633,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1953-07-05",
  "time": "23:46",
  "lat": 19.0760,
  "lon": 72.8777,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1993-10-29",
  "time": "03:42",
  "lat": 14.5995,
  "lon": 120.9842,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2007-04-08",
  "time": "18:36",
  "lat": 35.1796,
  "lon": 129.0756,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1937-08-11",
  "time": "16:59",
  "lat": -22.9068,
  "lon": -43.1729,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1977-01-02",
  "time": "07:55",
  "lat": 12.9716,
  "lon": 77.5946,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1942-05-24",
  "time": "20:16",
  "lat": 60.1699,
  "lon": 24.9384,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1965-11-17",
  "time": "10:12",
  "lat": -41.2865,
  "lon": 174.7762,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2002-08-23",
  "time": "01:58",
  "lat": 41.7151,
  "lon": 44.8271,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2015-01-27",
  "time": "06:44",
  "lat": -15.7975,
  "lon": -47.8919,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1956-09-21",
  "time": "22:30",
  "lat": 50.1109,
  "lon": 8.6821,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1989-06-04",
  "time": "04:55",
  "lat": 28.6139,
  "lon": 77.2090,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1934-10-19",
  "time": "11:21",
  "lat": -4.4419,
  "lon": 15.2663,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1960-12-06",
  "time": "14:47",
  "lat": 43.6532,
  "lon": -79.3832,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1982-02-28",
  "time": "09:31",
  "lat": 25.2769,
  "lon": 55.2962,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2006-03-15",
  "time": "21:14",
  "lat": -12.0464,
  "lon": -77.0428,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2019-09-01",
  "time": "16:29",
  "lat": 45.4642,
  "lon": 9.1900,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1947-06-09",
  "time": "12:36",
  "lat": 64.1355,
  "lon": -21.8954,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1972-03-28",
  "time": "19:49",
  "lat": 35.9078,
  "lon": 127.7669,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1996-12-14",
  "time": "02:20",
  "lat": -17.7134,
  "lon": 178.0650,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2012-07-07",
  "time": "08:59",
  "lat": 19.0760,
  "lon": 72.8777,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1954-05-05",
  "time": "23:15",
  "lat": -25.7461,
  "lon": 28.1881,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1988-11-30",
  "time": "06:41",
  "lat": 14.5995,
  "lon": 120.9842,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1939-02-08",
  "time": "03:56",
  "lat": 37.5665,
  "lon": 126.9780,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1979-08-02",
  "time": "17:38",
  "lat": 34.0522,
  "lon": -118.2437,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2004-04-22",
  "time": "05:27",
  "lat": 60.1699,
  "lon": 24.9384,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "2011-10-18",
  "time": "13:02",
  "lat": 64.9631,
  "lon": -19.0208,
  "country": "",
  "state": ""
}
{
  "name": "",
  "date": "1943-09-27",
  "time": "22:41",
  "lat": -15.7975,
  "lon": -47.8919,
  "country": "",
  "state": ""
}
'''
    
    # =============================================================================
    # CONFIGURATION - Adjust these settings as needed
    # =============================================================================
    
    # Delay between analyses (seconds) - adjust based on your system
    delay_between_analyses = 0.5  # Start with 0.5, reduce if system is fast
    
    # Output file names
    json_output_file = "custom_batch_results.json"
    csv_output_file = "custom_batch_summary.csv"
    
    # =============================================================================
    # MAIN PROCESSING - No need to modify below this line
    # =============================================================================
    
    print("🚀 PLUMATOTM CUSTOM BATCH PROCESSOR")
    print("=" * 60)
    print("⚠️  LOCAL TESTING ONLY - Does NOT impact Render API")
    print("=" * 60)
    
    # Initialize processor
    processor = CustomBatchProcessor()
    
    # Process the profiles
    results = processor.process_profiles_from_json(profiles_input, delay=delay_between_analyses)
    
    # Save results
    processor.save_results(results, json_output_file)
    processor.save_csv_summary(results, csv_output_file)
    
    # Print summary
    processor.print_summary(results)
    
    print(f"\n🎉 Custom batch processing completed!")
    print(f"💾 Results saved to outputs/{json_output_file}")
    print(f"📊 CSV summary saved to outputs/{csv_output_file}")
    print(f"⚠️  This was local testing only - Render API was NOT affected")

if __name__ == "__main__":
    main()
