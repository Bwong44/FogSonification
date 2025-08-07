#!/usr/bin/env python3
"""
3-Channel MIDI Generator with Sunrise/Sunset Events
==================================================
Convert cleaned CSV data to MIDI with three distinct channels:
1. Cloud Coverage (inverted) - Major pentatonic scale
2. Solar Sine Wave - Minor pentatonic scale (peaks at solar noon)
3. Sunrise/Sunset Events - Harmonic minor scale (only plays during actual events)

Usage:
    python cleaned_to_midi_3ch_events.py data_cleaned.csv
    python cleaned_to_midi_3ch_events.py data_cleaned.csv --bpm 120 --duration 300
"""

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from midiutil import MIDIFile
import sys
import os
from datetime import datetime

def create_3channel_midi_with_events(csv_file, bpm=120, duration=300, auto_duration=False, output_file=None, verbose=False):
    """
    Convert CSV data to 3-channel MIDI with sunrise/sunset events.
    
    Args:
        csv_file (str): Path to cleaned CSV file
        bpm (int): Beats per minute (60-240)
        duration (int): Duration in seconds (60-600) 
        auto_duration (bool): Calculate duration to maintain musical density
        output_file (str): Output MIDI file path (optional)
        verbose (bool): Print detailed information
    
    Returns:
        str: Path to output MIDI file
    """
    
    if verbose:
        print(f"Loading data from: {csv_file}")
        print(f"Target BPM: {bpm}")
        if auto_duration:
            print("Auto-duration: ON (maintaining musical density)")
        else:
            print(f"Duration: {duration} seconds")
    
    # Load and validate data
    try:
        df = pd.read_csv(csv_file)
        if verbose:
            print(f"Loaded {len(df)} data points")
            print(f"Columns: {list(df.columns)}")
    except Exception as e:
        raise ValueError(f"Error loading CSV: {e}")
    
    # Validate required columns
    required_cols = ['cloud_cover_low (%)', 'solar_sine', 'sunrise_event', 'sunset_event']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter data and create events
    if verbose:
        print("Processing data channels...")
    
    # Channel 1: Cloud coverage (inverted - less clouds = higher notes)
    cloud_data = 100 - df['cloud_cover_low (%)'].fillna(0)  # Invert so clear sky = high notes
    cloud_data = np.clip(cloud_data, 0, 100)
    
    # Channel 2: Solar sine wave (0-6, peaks at solar noon)
    solar_data = df['solar_sine'].fillna(3)  # Default to middle value if missing
    solar_data = np.clip(solar_data, 0, 6)
    
    # Channel 3: Sunrise/sunset events (only active during actual events)
    sunrise_events = df['sunrise_event'].fillna(False)
    sunset_events = df['sunset_event'].fillna(False)
    
    # Count events
    sunrise_count = sunrise_events.sum()
    sunset_count = sunset_events.sum()
    total_events = sunrise_count + sunset_count
    
    if verbose:
        print(f"Cloud coverage range: {df['cloud_cover_low (%)'].min():.1f}% - {df['cloud_cover_low (%)'].max():.1f}%")
        print(f"Solar sine range: {solar_data.min():.2f} - {solar_data.max():.2f}")
        print(f"Sunrise events: {sunrise_count}")
        print(f"Sunset events: {sunset_count}")
        print(f"Total solar events: {total_events}")
    
    # Calculate timing
    data_points = len(df)
    
    if auto_duration:
        # Maintain musical density: ~4 notes per second across all channels
        target_notes_per_second = 4
        calculated_duration = (data_points * 3) / target_notes_per_second  # 3 channels
        duration = int(calculated_duration)
        if verbose:
            print(f"Auto-calculated duration: {duration} seconds ({calculated_duration:.1f})")
    
    # Calculate note timing
    beats_per_second = bpm / 60
    total_beats = duration * beats_per_second
    beats_per_note = total_beats / data_points
    
    if verbose:
        print(f"Musical timing:")
        print(f"  Total beats: {total_beats:.1f}")
        print(f"  Beats per data point: {beats_per_note:.3f}")
        print(f"  Notes per second: {data_points / duration:.2f}")
    
    # Define musical scales (MIDI note numbers)
    
    # Channel 1: Major pentatonic (bright, clear sky feeling)
    major_pentatonic = [60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84, 86, 88]  # C major pentatonic
    
    # Channel 2: Minor pentatonic (time cycle feeling)  
    minor_pentatonic = [48, 51, 53, 55, 58, 60, 63, 65, 67, 70, 72, 75, 77]  # C minor pentatonic
    
    # Channel 3: Harmonic minor (dramatic sunrise/sunset feeling)
    harmonic_minor = [36, 38, 39, 42, 44, 45, 48, 50, 51, 54, 56, 57, 60]  # C harmonic minor
    
    # Create MIDI file
    midi = MIDIFile(3)  # 3 tracks
    track_time = 0
    
    # Track 0: Cloud coverage channel
    midi.addTrackName(track=0, time=0, trackName="Cloud Coverage (Inverted)")
    midi.addTempo(track=0, time=0, tempo=bpm)
    midi.addProgramChange(tracknum=0, channel=0, time=0, program=0)  # Piano
    
    # Track 1: Solar sine wave channel  
    midi.addTrackName(track=1, time=0, trackName="Solar Sine Wave")
    midi.addTempo(track=1, time=0, tempo=bpm)
    midi.addProgramChange(tracknum=1, channel=1, time=0, program=8)  # Celesta
    
    # Track 2: Sunrise/Sunset events
    midi.addTrackName(track=2, time=0, trackName="Sunrise/Sunset Events")
    midi.addTempo(track=2, time=0, tempo=bpm)
    midi.addProgramChange(tracknum=2, channel=2, time=0, program=14)  # Tubular bells
    
    # Generate notes
    current_beat = 0
    
    if verbose:
        print("Generating MIDI notes...")
    
    for i, row in df.iterrows():
        # Channel 1: Cloud coverage (inverted)
        cloud_pct = cloud_data.iloc[i]
        cloud_note_idx = int((cloud_pct / 100) * (len(major_pentatonic) - 1))
        cloud_note = major_pentatonic[cloud_note_idx]
        cloud_velocity = int(50 + (cloud_pct / 100) * 50)  # 50-100 velocity
        
        midi.addNote(track=0, channel=0, pitch=cloud_note, time=current_beat, 
                    duration=beats_per_note * 0.8, volume=cloud_velocity)
        
        # Channel 2: Solar sine wave (peaks at solar noon)
        solar_val = solar_data.iloc[i]
        solar_note_idx = int((solar_val / 6) * (len(minor_pentatonic) - 1))
        solar_note = minor_pentatonic[solar_note_idx]
        solar_velocity = int(40 + (solar_val / 6) * 40)  # 40-80 velocity
        
        midi.addNote(track=1, channel=1, pitch=solar_note, time=current_beat,
                    duration=beats_per_note * 0.7, volume=solar_velocity)
        
        # Channel 3: Sunrise/Sunset events (only during actual events)
        is_sunrise = sunrise_events.iloc[i]
        is_sunset = sunset_events.iloc[i]
        
        if is_sunrise or is_sunset:
            # Choose note based on event type
            if is_sunrise:
                # Rising notes for sunrise
                event_note_idx = len(harmonic_minor) - 3  # Higher notes
                event_velocity = 100  # Strong for sunrise
            else:  # sunset
                # Lower notes for sunset (moved up one note)
                event_note_idx = 3  # One note higher than before
                event_velocity = 80  # Softer for sunset
            
            event_note = harmonic_minor[event_note_idx]
            
            midi.addNote(track=2, channel=2, pitch=event_note, time=current_beat,
                        duration=beats_per_note * 1.2, volume=event_velocity)
        
        current_beat += beats_per_note
    
    # Generate output filename if not provided
    if output_file is None:
        base_name = os.path.splitext(csv_file)[0]
        if auto_duration:
            output_file = f"{base_name}_3ch_events_{bpm}bpm_auto.mid"
        else:
            output_file = f"{base_name}_3ch_events_{bpm}bpm_{duration}s.mid"
    
    # Save MIDI file
    try:
        with open(output_file, "wb") as midi_file:
            midi.writeFile(midi_file)
        if verbose:
            print(f"MIDI file saved: {output_file}")
    except Exception as e:
        raise ValueError(f"Error saving MIDI file: {e}")
    
    # Create visualization
    create_visualization(df, cloud_data, solar_data, sunrise_events, sunset_events, 
                        output_file, duration, bpm, verbose)
    
    return output_file

def create_visualization(df, cloud_data, solar_data, sunrise_events, sunset_events, 
                        midi_file, duration, bpm, verbose=False):
    """Create visualization of the 3-channel data."""
    
    if verbose:
        print("Creating visualization...")
    
    # Create time axis
    time_points = np.linspace(0, duration, len(df))
    
    # Create figure with 4 subplots
    fig, axes = plt.subplots(4, 1, figsize=(15, 12))
    fig.suptitle(f'3-Channel MIDI Data: {bpm} BPM, {duration}s duration', fontsize=16)
    
    # Plot 1: Original cloud coverage
    axes[0].plot(time_points, df['cloud_cover_low (%)'], 'b-', alpha=0.7, linewidth=1)
    axes[0].set_ylabel('Cloud Coverage (%)', fontsize=12)
    axes[0].set_title('Channel 1: Cloud Coverage (Original)', fontsize=14)
    axes[0].grid(True, alpha=0.3)
    axes[0].set_ylim(0, 100)
    
    # Plot 2: Inverted cloud data (what actually gets played)
    axes[1].plot(time_points, cloud_data, 'g-', alpha=0.7, linewidth=1)
    axes[1].set_ylabel('Inverted Cloud (%)', fontsize=12)
    axes[1].set_title('Channel 1: Inverted Cloud Coverage (Higher = Clearer Sky)', fontsize=14)
    axes[1].grid(True, alpha=0.3)
    axes[1].set_ylim(0, 100)
    
    # Plot 3: Solar sine wave
    axes[2].plot(time_points, solar_data, 'orange', alpha=0.7, linewidth=1)
    axes[2].set_ylabel('Solar Sine (0-6)', fontsize=12)
    axes[2].set_title('Channel 2: Solar Sine Wave (Peaks at Solar Noon)', fontsize=14)
    axes[2].grid(True, alpha=0.3)
    axes[2].set_ylim(0, 6)
    
    # Plot 4: Sunrise/Sunset events
    sunrise_times = time_points[sunrise_events]
    sunset_times = time_points[sunset_events]
    
    axes[3].scatter(sunrise_times, [1]*len(sunrise_times), color='gold', s=50, alpha=0.8, label='Sunrise', marker='^')
    axes[3].scatter(sunset_times, [0]*len(sunset_times), color='purple', s=50, alpha=0.8, label='Sunset', marker='v')
    axes[3].set_ylabel('Event Type', fontsize=12)
    axes[3].set_title('Channel 3: Sunrise/Sunset Events', fontsize=14)
    axes[3].set_xlabel('Time (seconds)', fontsize=12)
    axes[3].grid(True, alpha=0.3)
    axes[3].set_ylim(-0.5, 1.5)
    axes[3].set_yticks([0, 1])
    axes[3].set_yticklabels(['Sunset', 'Sunrise'])
    axes[3].legend()
    
    # Adjust layout and save
    plt.tight_layout()
    
    # Generate visualization filename
    viz_file = midi_file.replace('.mid', '_visualization.png')
    plt.savefig(viz_file, dpi=150, bbox_inches='tight')
    
    if verbose:
        print(f"Visualization saved: {viz_file}")
    
    plt.close()

def main():
    parser = argparse.ArgumentParser(
        description="Convert cleaned CSV to 3-channel MIDI with sunrise/sunset events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i data_cleaned.csv                           # Default: 120 BPM, 300s
  %(prog)s -i data_cleaned.csv --bpm 80 --duration 240  # Custom BPM and duration  
  %(prog)s -i data_cleaned.csv --auto-duration          # Auto-calculate duration
  %(prog)s -i data_cleaned.csv -o my_song.mid           # Custom output filename
  %(prog)s -i data_cleaned.csv -v                       # Verbose output
        """
    )
    
    # Required argument
    parser.add_argument('-i', '--input', dest='csv_file', required=True,
                       help='Cleaned CSV file to convert')
    
    # Optional arguments
    parser.add_argument('-o', '--output', dest='output_file',
                       help='Output MIDI file (default: auto-generated)')
    
    parser.add_argument('--bpm', type=int, default=120,
                       help='Beats per minute (60-240, default: 120)')
    
    parser.add_argument('--duration', type=int, default=300,
                       help='Duration in seconds (60-600, default: 300)')
    
    parser.add_argument('--auto-duration', action='store_true',
                       help='Auto-calculate duration to maintain musical density')
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Print detailed information')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate arguments
    if args.bpm < 60 or args.bpm > 240:
        parser.error("BPM must be between 60 and 240")
    
    if args.duration < 60 or args.duration > 600:
        parser.error("Duration must be between 60 and 600 seconds")
    
    try:
        # Convert to MIDI
        output_path = create_3channel_midi_with_events(
            csv_file=args.csv_file,
            bpm=args.bpm,
            duration=args.duration,
            auto_duration=args.auto_duration,
            output_file=args.output_file,
            verbose=args.verbose
        )
        
        print(f"\nMIDI conversion complete!")
        print(f"Output file: {output_path}")
        
        # Show file size
        file_size = os.path.getsize(output_path)
        print(f"File size: {file_size:,} bytes")
        
        # Show visualization file
        viz_file = output_path.replace('.mid', '_visualization.png')
        if os.path.exists(viz_file):
            print(f"Visualization: {viz_file}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
