#!/usr/bin/env python3
"""
CSV Cleanup Script with Solar-based Sine Wave
==============================================
Flexible script to clean up CSV files with weather/time series data and create 
sine wave patterns based on actual sunrise/sunset times.

Features:
- Remove header lines (configurable)
- Separate date and time from datetime column
- Extract sunrise/sunset data from multi-section CSV
- Create solar-aligned sine wave (peaks at solar noon, lowest at solar midnight)
- Handle various CSV formats

Usage:
    python csv_cleanup.py input.csv -o output.csv
    python csv_cleanup.py input.csv --skip-lines 3 --sine-range 6
"""

import argparse
import pandas as pd
import sys
import os
import math
from datetime import datetime, timedelta

def extract_solar_data(lines, verbose=False):
    """
    Extract sunrise/sunset data from the CSV lines.
    
    Args:
        lines: List of all lines from the CSV file
        verbose: Print detailed information
    
    Returns:
        DataFrame with date, sunrise, sunset columns
    """
    # Find the solar data section
    solar_start = None
    for i, line in enumerate(lines):
        if 'sunrise' in line.lower() and 'sunset' in line.lower():
            solar_start = i
            break
    
    if solar_start is None:
        if verbose:
            print("No sunrise/sunset data found - will use fixed day/night cycles")
        return None
    
    if verbose:
        print(f"Found solar data starting at line {solar_start + 1}")
    
    # Read solar data section
    solar_lines = lines[solar_start:]
    
    # Create temp file for solar data
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
        temp_file.writelines(solar_lines)
        temp_filename = temp_file.name
    
    try:
        solar_df = pd.read_csv(temp_filename)
        if verbose:
            print(f"Loaded {len(solar_df)} solar data rows")
            print(f"Solar columns: {list(solar_df.columns)}")
        
        # Parse the solar times
        solar_df['date'] = pd.to_datetime(solar_df['time']).dt.date
        solar_df['sunrise_time'] = pd.to_datetime(solar_df['sunrise (iso8601)'])
        solar_df['sunset_time'] = pd.to_datetime(solar_df['sunset (iso8601)'])
        
        # Calculate solar noon (midpoint between sunrise and sunset)
        solar_df['solar_noon'] = solar_df['sunrise_time'] + (solar_df['sunset_time'] - solar_df['sunrise_time']) / 2
        
        if verbose:
            print("Sample solar data:")
            print(solar_df[['date', 'sunrise_time', 'sunset_time', 'solar_noon']].head())
        
        return solar_df[['date', 'sunrise_time', 'sunset_time', 'solar_noon']]
        
    finally:
        os.unlink(temp_filename)

def calculate_realistic_solar_noon_offset(day_of_year, longitude=-122.02):
    """
    Calculate realistic solar noon offset based on:
    1. Equation of Time (Earth's elliptical orbit + axial tilt)
    2. Longitude offset from time zone meridian
    
    Args:
        day_of_year: Day of year (1-366)
        longitude: Longitude in degrees (Santa Cruz ~-122.02)
    
    Returns:
        float: Minutes offset from 12:00 noon
    """
    
    # Equation of Time calculation (simplified)
    # This accounts for Earth's elliptical orbit and axial tilt
    B = 2 * math.pi * (day_of_year - 81) / 365
    E = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)
    
    # Longitude correction (PST time zone meridian is -120°)
    # Santa Cruz is at -122.02°, so it's 2.02° west of time zone center
    time_zone_meridian = -120  # PST meridian
    longitude_offset_minutes = 4 * (longitude - time_zone_meridian)  # 4 minutes per degree
    
    # Total offset in minutes
    total_offset_minutes = E + longitude_offset_minutes
    
    return total_offset_minutes

def calculate_sunrise_sunset_events(datetime_obj, solar_data, tolerance_minutes=30, verbose=False):
    """
    Check if the given datetime is at or near actual sunrise/sunset time.
    
    Args:
        datetime_obj: pandas datetime object
        solar_data: DataFrame with solar times for each date
        tolerance_minutes: How close to sunrise/sunset to mark as event (default: 30 minutes)
        verbose: Print debug info
    
    Returns:
        tuple: (is_sunrise, is_sunset) - boolean flags for actual events
    """
    if solar_data is None:
        # Fallback: assume 6:00 AM sunrise, 6:00 PM sunset
        hour = datetime_obj.hour
        minute = datetime_obj.minute
        current_minutes = hour * 60 + minute
        
        sunrise_minutes = 6 * 60  # 6:00 AM
        sunset_minutes = 18 * 60  # 6:00 PM
        
        # Check if within tolerance of sunrise or sunset
        is_sunrise = abs(current_minutes - sunrise_minutes) <= tolerance_minutes
        is_sunset = abs(current_minutes - sunset_minutes) <= tolerance_minutes
        
        return is_sunrise, is_sunset
    
    # Find solar data for this date
    date = datetime_obj.date()
    solar_row = solar_data[solar_data['date'] == date]
    
    if solar_row.empty:
        if verbose:
            print(f"No solar data found for {date}, using fallback")
        return calculate_sunrise_sunset_events(datetime_obj, None, tolerance_minutes, verbose)
    
    solar_row = solar_row.iloc[0]
    sunrise_time = solar_row['sunrise_time']
    sunset_time = solar_row['sunset_time']
    
    # Calculate time differences in minutes
    current_time = datetime_obj
    sunrise_diff_minutes = abs((current_time - sunrise_time).total_seconds() / 60)
    sunset_diff_minutes = abs((current_time - sunset_time).total_seconds() / 60)
    
    # Check if within tolerance
    is_sunrise = sunrise_diff_minutes <= tolerance_minutes
    is_sunset = sunset_diff_minutes <= tolerance_minutes
    
    if verbose and (is_sunrise or is_sunset):
        sunrise_str = f"SUNRISE ({sunrise_diff_minutes:.0f}m)" if is_sunrise else ""
        sunset_str = f"SUNSET ({sunset_diff_minutes:.0f}m)" if is_sunset else ""
        event_str = " ".join(filter(None, [sunrise_str, sunset_str]))
        print(f"  {current_time.strftime('%H:%M')}: {event_str}")
    
    return is_sunrise, is_sunset

def calculate_solar_sine_wave(datetime_obj, solar_data, sine_range=6, verbose=False, use_realistic_timing=True):
    """
    Calculate sine wave value based on solar position for a given datetime.
    
    Args:
        datetime_obj: pandas datetime object
        solar_data: DataFrame with solar times for each date (can be None)
        sine_range: Maximum value of sine wave (peak at solar noon)
        verbose: Print debug info for first few calculations
        use_realistic_timing: Use realistic seasonal solar noon variations
    
    Returns:
        float: Sine wave value (0 to sine_range)
    """
    date = datetime_obj.date()
    hour = datetime_obj.hour + datetime_obj.minute / 60.0
    day_of_year = datetime_obj.timetuple().tm_yday
    
    if use_realistic_timing:
        # Use realistic seasonal solar timing
        solar_noon_offset_minutes = calculate_realistic_solar_noon_offset(day_of_year)
        solar_noon_hour = 12 + (solar_noon_offset_minutes / 60)  # Convert to decimal hours
        
        # Create sine wave centered on realistic solar noon
        hours_from_solar_noon = hour - solar_noon_hour
        
        # Handle day wrapping
        if hours_from_solar_noon > 12:
            hours_from_solar_noon -= 24
        elif hours_from_solar_noon < -12:
            hours_from_solar_noon += 24
        
        # Sine wave: peaks at solar noon (0 hours from noon), minimum at solar midnight (±12 hours)
        sine_value = sine_range/2 + sine_range/2 * math.cos(2 * math.pi * hours_from_solar_noon / 24)
        
        if verbose:
            print(f"    Realistic timing: Solar noon at {solar_noon_hour:.2f}, offset {solar_noon_offset_minutes:.1f} min")
        
        return max(0, min(sine_range, sine_value))
    
    # Find solar data for this date if available
    if solar_data is not None:
        solar_row = solar_data[solar_data['date'] == date]
        
        if not solar_row.empty:
            sunrise = solar_row['sunrise_time'].iloc[0]
            sunset = solar_row['sunset_time'].iloc[0]
            solar_noon = solar_row['solar_noon'].iloc[0]
            
            # Calculate time since solar midnight (opposite of solar noon)
            # Solar midnight is 12 hours from solar noon
            solar_midnight = solar_noon - timedelta(hours=12)
            if solar_midnight.date() != date:
                solar_midnight = solar_noon + timedelta(hours=12)
            
            # Calculate hours since solar midnight
            time_diff = datetime_obj - solar_midnight
            hours_since_midnight = time_diff.total_seconds() / 3600
            
            # Handle day wrapping
            if hours_since_midnight < 0:
                hours_since_midnight += 24
            elif hours_since_midnight >= 24:
                hours_since_midnight -= 24
            
            # Create sine wave that peaks at solar noon (12 hours from solar midnight)
            # and is lowest at solar midnight (0 and 24 hours)
            sine_value = sine_range/2 + sine_range/2 * math.sin(2 * math.pi * hours_since_midnight / 24 - math.pi / 2)
            
            return max(0, min(sine_range, sine_value))
    
    # Fallback to fixed calculation if no solar data
    # Assume 6:00 AM sunrise, 6:00 PM sunset for fallback
    return sine_range/2 + sine_range/2 * math.sin(2 * math.pi * (hour - 6) / 24 + math.pi / 2)

def cleanup_csv(input_file, output_file=None, skip_lines=3, day_start=6, day_end=20, 
                sine_range=6, use_solar=True, use_realistic_timing=True, tolerance_minutes=30, verbose=False):
    """
    Clean up CSV file and create solar-aligned sine wave patterns.
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file (optional)
        skip_lines (int): Number of lines to skip from beginning (default: 3)
        day_start (int): Hour when day cycle starts (fallback, default: 6)
        day_end (int): Hour when day cycle ends (fallback, default: 20) 
        sine_range (float): Maximum sine wave value (default: 6)
        use_solar (bool): Use actual sunrise/sunset data if available
        use_realistic_timing (bool): Use realistic seasonal solar noon variations
        tolerance_minutes (int): Minutes tolerance for sunrise/sunset events (default: 30)
        verbose (bool): Print detailed information
    
    Returns:
        str: Path to output file
    """
    
    if verbose:
        print(f"Processing: {input_file}")
        print(f"Skipping first {skip_lines} lines")
        if use_realistic_timing:
            print(f"Using realistic seasonal solar timing (range: 0-{sine_range})")
        elif use_solar:
            print(f"Using solar data for sine wave (range: 0-{sine_range})")
        else:
            print(f"Using fixed day cycle: {day_start}:00 - {day_end}:00")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Read the file and find data sections
    try:
        # Read all lines first to detect structure
        with open(input_file, 'r') as f:
            lines = f.readlines()
        
        if verbose:
            print(f"Total lines in file: {len(lines)}")
        
        # Extract solar data if available and requested
        solar_data = None
        if use_solar:
            solar_data = extract_solar_data(lines, verbose)
        
        # Find the main data section (after skipping header lines)
        data_start = skip_lines
        data_end = len(lines)
        
        # Look for section breaks (empty lines or new headers)
        for i in range(skip_lines, len(lines)):
            line = lines[i].strip()
            # If we find an empty line or a line that looks like a header, stop
            if not line or (line.count(',') > 0 and 'time' in line.lower() and i > skip_lines + 10):
                data_end = i
                break
        
        if verbose:
            print(f"Weather data section: lines {data_start + 1} to {data_end}")
        
        # Read only the main data section
        data_lines = lines[data_start:data_end]
        
        # Create a temporary file with just the data section
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
            temp_file.writelines(data_lines)
            temp_filename = temp_file.name
        
        try:
            df = pd.read_csv(temp_filename)
            if verbose:
                print(f"Loaded {len(df)} data rows")
                print(f"Columns: {list(df.columns)}")
        finally:
            # Clean up temp file
            os.unlink(temp_filename)
            
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")
    
    # Find the time/datetime column (look for common patterns)
    time_column = None
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['time', 'date', 'timestamp']):
            time_column = col
            break
    
    if time_column is None:
        # Try to find datetime-like data in first column
        if len(df.columns) > 0:
            first_col = df.columns[0]
            # Check if first column contains datetime-like strings
            sample_value = str(df[first_col].iloc[0])
            if 'T' in sample_value or '-' in sample_value:
                time_column = first_col
                if verbose:
                    print(f"Auto-detected time column: {first_col}")
    
    if time_column is None:
        raise ValueError("Could not find time/datetime column. Please check your CSV format.")
    
    if verbose:
        print(f"Using time column: {time_column}")
        print(f"Sample time value: {df[time_column].iloc[0]}")
    
    # Parse datetime and extract components
    try:
        df['datetime'] = pd.to_datetime(df[time_column])
        df['date'] = df['datetime'].dt.date
        df['time'] = df['datetime'].dt.strftime('%H:%M')
        df['hour'] = df['datetime'].dt.hour
        
        if verbose:
            print("Successfully parsed datetime components")
    except Exception as e:
        raise ValueError(f"Error parsing datetime column '{time_column}': {e}")
    
    # Create solar-aligned sine wave or fallback day/night cycle
    if use_realistic_timing or (solar_data is not None and use_solar):
        if verbose:
            timing_method = "realistic seasonal" if use_realistic_timing else "solar data"
            print(f"Calculating {timing_method} sine wave and sunrise/sunset proximity...")
        
        # Calculate sine wave and sunrise/sunset events for each data point
        sine_values = []
        sunrise_events = []
        sunset_events = []
        
        for idx, row in df.iterrows():
            sine_val = calculate_solar_sine_wave(
                row['datetime'], 
                solar_data, 
                sine_range, 
                verbose=(idx < 5),  # Verbose for first 5 rows
                use_realistic_timing=use_realistic_timing
            )
            sine_values.append(round(sine_val, 2))
            
            # Check for actual sunrise/sunset events
            is_sunrise, is_sunset = calculate_sunrise_sunset_events(
                row['datetime'],
                solar_data,
                tolerance_minutes=tolerance_minutes,  # Use parameter
                verbose=(idx < 20 and (idx % 5 == 0))  # Verbose for some rows
            )
            sunrise_events.append(is_sunrise)
            sunset_events.append(is_sunset)
        
        df['solar_sine'] = sine_values
        df['sunrise_event'] = sunrise_events
        df['sunset_event'] = sunset_events
        
        # Also create traditional day/night cycle for comparison
        df['cycle'] = df['hour'].apply(
            lambda h: 'day' if day_start <= h < day_end else 'night'
        )
        
        if verbose:
            print(f"Solar sine wave stats:")
            print(f"  Min: {min(sine_values):.2f}")
            print(f"  Max: {max(sine_values):.2f}")
            print(f"  Range: 0 to {sine_range}")
            
            sunrise_count = sum(sunrise_events)
            sunset_count = sum(sunset_events)
            print(f"Sunrise events: {sunrise_count}")
            print(f"Sunset events: {sunset_count}")
            
            if use_realistic_timing:
                # Show seasonal variation info
                print(f"  Seasonal solar noon variation:")
                sample_days = [15, 106, 197, 289]  # Mid-Jan, Apr, Jul, Oct
                for doy in sample_days:
                    offset = calculate_realistic_solar_noon_offset(doy)
                    solar_noon_time = 12 + (offset / 60)
                    hour = int(solar_noon_time)
                    minute = int((solar_noon_time - hour) * 60)
                    season = ["Winter", "Spring", "Summer", "Fall"][sample_days.index(doy)]
                    print(f"    {season}: Solar noon ~{hour:02d}:{minute:02d} ({offset:+.1f} min)")
            
    else:
        if verbose:
            print("Using traditional day/night cycle...")
        
        # Create traditional day/night cycle column
        df['cycle'] = df['hour'].apply(
            lambda h: 'day' if day_start <= h < day_end else 'night'
        )
        
        # Create simple sine wave based on hour
        df['solar_sine'] = df['hour'].apply(
            lambda h: round(sine_range/2 + sine_range/2 * math.sin(2 * math.pi * (h - 6) / 24 + math.pi / 2), 2)
        )
        
        # Create simple sunrise/sunset events based on fixed times
        sunrise_events = []
        sunset_events = []
        for _, row in df.iterrows():
            is_sunrise, is_sunset = calculate_sunrise_sunset_events(row['datetime'], None, tolerance_minutes=tolerance_minutes)
            sunrise_events.append(is_sunrise)
            sunset_events.append(is_sunset)
        
        df['sunrise_event'] = sunrise_events
        df['sunset_event'] = sunset_events
    
    # Count cycles
    day_count = (df['cycle'] == 'day').sum()
    night_count = (df['cycle'] == 'night').sum()
    
    if verbose:
        print(f"Day cycle ({day_start}:00-{day_end}:00): {day_count} data points")
        print(f"Night cycle: {night_count} data points")
    
    # Create output dataframe with desired columns
    output_columns = ['date', 'time', 'hour', 'cycle', 'solar_sine', 'sunrise_event', 'sunset_event']
    
    # Add other data columns (excluding the original time column)
    for col in df.columns:
        if col not in [time_column, 'datetime', 'date', 'time', 'hour', 'cycle', 'solar_sine', 'sunrise_event', 'sunset_event']:
            output_columns.append(col)
    
    df_cleaned = df[output_columns].copy()
    
    # Generate output filename if not provided
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_cleaned.csv"
    
    # Save the cleaned data
    try:
        df_cleaned.to_csv(output_file, index=False)
        if verbose:
            print(f"Saved cleaned data to: {output_file}")
            print(f"Output columns: {list(df_cleaned.columns)}")
            print(f"First few rows:")
            print(df_cleaned.head())
    except Exception as e:
        raise ValueError(f"Error saving output file: {e}")
    
    return output_file

def main():
    parser = argparse.ArgumentParser(
        description="Clean up CSV files with weather/time series data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i data.csv                                    # Basic cleanup with realistic solar timing
  %(prog)s -i data.csv -o clean_data.csv                 # Specify output file
  %(prog)s -i data.csv --skip-lines 5                    # Skip 5 header lines
  %(prog)s -i data.csv --day-start 7 --day-end 19        # Day cycle 7:00-19:00
  %(prog)s -i data.csv --no-realistic-timing             # Use simple solar model
  %(prog)s -i data.csv --use-solar                       # Use CSV solar data if available
  %(prog)s -i data.csv --tolerance 15                    # 15-minute window for sunrise/sunset events
  %(prog)s -i data.csv -v                                # Verbose output
  %(prog)s -i data.csv --skip-lines 0                    # Don't skip any lines
        """
    )
    
    # Required argument
    parser.add_argument('-i', '--input', dest='input_file', required=True,
                       help='Input CSV file to clean up')
    
    # Optional arguments
    parser.add_argument('-o', '--output', 
                       dest='output_file',
                       help='Output CSV file (default: input_cleaned.csv)')
    
    parser.add_argument('--skip-lines', 
                       type=int, 
                       default=3,
                       help='Number of lines to skip from beginning (default: 3)')
    
    parser.add_argument('--day-start', 
                       type=int, 
                       default=6,
                       help='Hour when day cycle starts (0-23, default: 6)')
    
    parser.add_argument('--day-end', 
                       type=int, 
                       default=20,
                       help='Hour when day cycle ends (0-23, default: 20)')
    
    parser.add_argument('-v', '--verbose', 
                       action='store_true',
                       help='Print detailed information')
                       
    parser.add_argument('--use-solar', 
                       action='store_true',
                       help='Use solar data to create realistic day/night sine waves (requires CSV with solar data)')
                       
    parser.add_argument('--use-realistic-timing', 
                       action='store_true',
                       default=True,
                       help='Use realistic seasonal solar noon variations (default: True)')
                       
    parser.add_argument('--no-realistic-timing', 
                       action='store_false',
                       dest='use_realistic_timing',
                       help='Disable realistic solar timing (use simple model)')
                       
    parser.add_argument('--sine-range', 
                       type=int, 
                       default=6,
                       help='Maximum value for sine wave (default: 6)')
    
    parser.add_argument('--tolerance', 
                       type=int, 
                       default=30,
                       help='Minutes tolerance for sunrise/sunset events (default: 30)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate arguments
    if args.day_start < 0 or args.day_start > 23:
        parser.error("day-start must be between 0 and 23")
    
    if args.day_end < 0 or args.day_end > 23:
        parser.error("day-end must be between 0 and 23")
    
    if args.day_start >= args.day_end:
        parser.error("day-start must be less than day-end")
    
    if args.sine_range < 1:
        parser.error("sine-range must be 1 or greater")

    try:
        # Run the cleanup
        output_path = cleanup_csv(
            input_file=args.input_file,
            output_file=args.output_file,
            skip_lines=args.skip_lines,
            day_start=args.day_start,
            day_end=args.day_end,
            use_solar=args.use_solar,
            use_realistic_timing=args.use_realistic_timing,
            sine_range=args.sine_range,
            tolerance_minutes=args.tolerance,
            verbose=args.verbose
        )
        
        print(f"\nCleanup complete!")
        print(f"Output file: {output_path}")
        
        # Show summary
        df_result = pd.read_csv(output_path)
        print(f"Summary:")
        print(f"   - Total rows: {len(df_result)}")
        print(f"   - Columns: {len(df_result.columns)}")
        print(f"   - Date range: {df_result['date'].min()} to {df_result['date'].max()}")
        
        day_count = (df_result['cycle'] == 'day').sum()
        night_count = (df_result['cycle'] == 'night').sum()
        print(f"   - Day cycle: {day_count} points ({day_count/len(df_result)*100:.1f}%)")
        print(f"   - Night cycle: {night_count} points ({night_count/len(df_result)*100:.1f}%)")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
