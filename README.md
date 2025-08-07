# Sonnification Pipeline

A data sonification pipeline that converts weather CSV data into 3-channel MIDI compositions, transforming cloud coverage and solar patterns into musical representations.

## What It Does

- **Cleans CSV weather data** with solar-aligned sine wave generation
- **Converts to 3-channel MIDI** with distinct musical scales for different data types
- **Preserves temporal relationships** through realistic solar timing
- **Detects sunrise/sunset events** for musical emphasis

## Quick Start

```bash
# Process weather data with solar timing
python csv_cleanup.py -i weather_data.csv --use-solar -v

# Convert to auto-timed MIDI
python cleaned_to_midi_3ch_events.py -i weather_data_cleaned.csv --auto-duration -v
```

## Table of Contents

- [CSV Cleanup Script](#csv-cleanup-script)
- [MIDI Generation Script](#midi-generation-script)  
- [Pipeline Examples](#pipeline-examples)
- [Musical Output](#musical-output)
- [Tips & Best Practices](#tips--best-practices)

---

## CSV Cleanup Script

Processes raw weather CSV files and generates solar-aligned data patterns.

### Usage
```bash
python csv_cleanup.py -i INPUT_FILE [OPTIONS]
```

### Arguments

#### Required
- `-i, --input` - Input CSV file to process

#### Optional
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `-o, --output` | path | `input_cleaned.csv` | Output file path |
| `--skip-lines` | int | `3` | Header lines to skip |
| `--day-start` | int | `6` | Day cycle start hour (0-23) |
| `--day-end` | int | `20` | Day cycle end hour (0-23) |
| `--sine-range` | int | `6` | Max sine wave value |
| `--tolerance` | int | `30` | Event detection window (minutes) |
| `--use-solar` | flag | `False` | Use CSV solar data |
| `--use-realistic-timing` | flag | `True` | Seasonal solar variations |
| `--no-realistic-timing` | flag | - | Disable realistic timing |
| `-v, --verbose` | flag | `False` | Detailed output |

### Examples

**Basic processing:**
```bash
python csv_cleanup.py -i data.csv --use-solar -v
```

**Custom event detection:**
```bash
python csv_cleanup.py -i data.csv --tolerance 15 --sine-range 8
```

**Extended day cycle:**
```bash
python csv_cleanup.py -i data.csv --day-start 5 --day-end 22
```

---

## MIDI Generation Script

Converts cleaned CSV data into 3-channel MIDI compositions.

### Usage
```bash
python cleaned_to_midi_3ch_events.py -i INPUT_FILE [OPTIONS]
```

### Arguments

#### Required
- `-i, --input` - Cleaned CSV file to convert

#### Optional
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `-o, --output` | path | auto-generated | Output MIDI file |
| `--bpm` | int | `120` | Beats per minute (60-240) |
| `--duration` | int | `300` | Length in seconds (60-600) |
| `--auto-duration` | flag | `False` | Calculate duration automatically |
| `-v, --verbose` | flag | `False` | Detailed output |

### Examples

**Auto-duration (recommended for full datasets):**
```bash
python cleaned_to_midi_3ch_events.py -i data_cleaned.csv --auto-duration -v
```

**Custom tempo and duration:**
```bash
python cleaned_to_midi_3ch_events.py -i data_cleaned.csv --bpm 80 --duration 240
```

**Quick preview:**
```bash
python cleaned_to_midi_3ch_events.py -i data_cleaned.csv --duration 60
```

---

## Pipeline Examples

### Complete Processing
```bash
# Full pipeline with solar timing
python csv_cleanup.py -i 2022Fog.csv --use-solar -v
python cleaned_to_midi_3ch_events.py -i 2022Fog_cleaned.csv --auto-duration -v
```

### Batch Processing
```bash
# Process multiple years
for year in 2022 2023 2024; do
    python csv_cleanup.py -i ${year}Fog.csv --use-solar -v
    python cleaned_to_midi_3ch_events.py -i ${year}Fog_cleaned.csv --auto-duration -v
done
```

### Preview Generation
```bash
# Create short previews
python csv_cleanup.py -i data.csv --use-solar
python cleaned_to_midi_3ch_events.py -i data_cleaned.csv --duration 120 --bpm 100
```

### One-Line Processing
```bash
python csv_cleanup.py -i data.csv --use-solar -v && \
python cleaned_to_midi_3ch_events.py -i data_cleaned.csv --auto-duration -v
```

---

## Musical Output

The pipeline generates 3-channel MIDI files with distinct musical characteristics:

### Channel Mapping
1. **Channel 1 - Cloud Coverage** 
   - Scale: Major pentatonic (C, D, E, G, A)
   - Data: Inverted cloud coverage percentage
   - Character: Bright, optimistic when clear

2. **Channel 2 - Solar Cycle**
   - Scale: Minor pentatonic (C, E♭, F, G, B♭)  
   - Data: Solar sine wave (peaks at solar noon)
   - Character: Natural daily rhythm

3. **Channel 3 - Solar Events**
   - Scale: Harmonic minor (C, D, E♭, F, G, A♭, B)
   - Data: Sunrise/sunset event detection
   - Character: Dramatic punctuation

### Output Files
- **MIDI file**: Multi-channel composition
- **Visualization**: PNG graph of all data channels
- **Console output**: Processing statistics and file info

---

## Tips & Best Practices

### Recommended Settings

**For weather data with solar information:**
```bash
python csv_cleanup.py -i data.csv --use-solar --use-realistic-timing -v
```

**For full datasets (months/years):**
```bash
python cleaned_to_midi_3ch_events.py -i data_cleaned.csv --auto-duration
```

**For precise event detection:**
```bash
python csv_cleanup.py -i data.csv --tolerance 15
```

### ⚡ Performance Tips

- Use `--auto-duration` for datasets with >1000 data points
- Start with `-v` verbose mode to understand processing
- Use appropriate tolerance: 15-30min for precision, 30-60min for broader detection
- For previews, use fixed duration (60-300 seconds)

### Data Requirements

- **CSV format** with datetime and numeric columns
- **Solar data** (optional): Enhances realism with actual sunrise/sunset times
- **Regular intervals**: Hourly data works best
- **Clean timestamps**: ISO format preferred (`YYYY-MM-DDTHH:MM`)

---

## Output Examples

### Duration Scaling
- **1 month** (744 hours) → ~9 minutes at auto-duration
- **1 year** (8760 hours) → ~1.8 hours at auto-duration  
- **Custom duration** → Compressed to specified length

### Musical Density
- **Auto-duration**: 1.33 notes per second (consistent across datasets)
- **Fixed duration**: Variable density based on data size
- **120 BPM default**: 2 beats per second timing base

---

## Data Sources

### Weather Data Credits
This project uses weather data provided by **[Open-Meteo](https://open-meteo.com/)**, a free weather API offering:

- **Historical weather data** with hourly resolution
- **Solar position calculations** including sunrise/sunset times
- **Multiple weather parameters** (cloud coverage, temperature, humidity, etc.)
- **Global coverage** with high-quality meteorological data
- **Free access** for research and educational purposes

We thank the Open-Meteo team for providing accessible, high-quality weather data that makes this sonification project possible.

**Example datasets used:**
- Santa Cruz, CA fog and cloud coverage data (2022-2025)
- Hourly weather observations with embedded solar data
- CSV format with ISO 8601 timestamps

---

## Future Work

### Planned Enhancements

#### API Integration
- **Open-Meteo API integration** for real-time data fetching
- **Location-based processing** using coordinates
- **Automated data updates** for continuous sonification
- **Multiple weather parameters** (temperature, humidity, wind)

#### Musical Improvements
- **Additional scales** and musical modes
- **Dynamic tempo changes** based on weather conditions
- **Polyphonic voice leading** for more complex compositions
- **Weather-specific instruments** (thunder sounds, wind effects)

#### Technical Features
- **Real-time streaming** MIDI generation
- **Web interface** for parameter adjustment
- **Batch processing** improvements
- **Docker containerization** for easy deployment

#### Data Processing
- **Multi-location sonification** (weather from multiple cities)
- **Seasonal pattern analysis** and musical representation
- **Weather prediction sonification** using forecast data
- **Climate change visualization** through long-term musical trends

#### User Experience
- **GUI application** for non-technical users
- **Web-based parameter tuning** interface
- **Audio playback** integration (not just MIDI export)
- **Interactive visualizations** with audio sync

### Contributing
Ideas and contributions for future enhancements are welcome! Areas of particular interest:
- Musical theory applications to weather data
- Additional weather parameter sonification
- Performance optimizations
- User interface improvements

---

### Basic Pipeline
```bash
# Step 1: Clean the CSV
python csv_cleanup.py -i raw_data.csv --use-solar -v

# Step 2: Convert to MIDI
python cleaned_to_midi_3ch_events.py -i raw_data_cleaned.csv --auto-duration -v
```

### Processing Multiple Years
```bash
# Process 2022 data
python csv_cleanup.py -i 2022Fog.csv --use-solar -v
python cleaned_to_midi_3ch_events.py -i 2022Fog_cleaned.csv --auto-duration -v

# Process 2023 data
python csv_cleanup.py -i 2023Fog.csv --use-solar -v
python cleaned_to_midi_3ch_events.py -i 2023Fog_cleaned.csv --auto-duration -v
```

### Custom Processing Pipeline
```bash
# Step 1: Clean with tight event detection
python csv_cleanup.py -i weather.csv --use-solar --tolerance 15 --sine-range 8 -v

# Step 2: Create short preview MIDI
python cleaned_to_midi_3ch_events.py -i weather_cleaned.csv --bpm 100 --duration 120 -v

# Step 3: Create full-length version
python cleaned_to_midi_3ch_events.py -i weather_cleaned.csv --auto-duration --bpm 100 -v
```

### One-Line Processing (with shell operators)
```bash
# Process and convert in one command
python csv_cleanup.py -i data.csv --use-solar -v && python cleaned_to_midi_3ch_events.py -i data_cleaned.csv --auto-duration -v
```

---

## Script Outputs

### CSV Cleanup Script Outputs
- **Cleaned CSV file**: Contains columns: `date`, `time`, `hour`, `cycle`, `solar_sine`, `sunrise_event`, `sunset_event`, plus original data columns
- **Console output**: Processing details, solar data info, event counts, summary statistics

### MIDI Generation Script Outputs
- **MIDI file**: 3-channel MIDI with cloud coverage (major pentatonic), solar sine (minor pentatonic), and events (harmonic minor)
- **Visualization PNG**: Graph showing all three data channels over time
- **Console output**: File size, duration, musical timing details

---

## Musical Scales Used

The MIDI generation uses these scales:

1. **Channel 1 (Cloud Coverage)**: Major pentatonic scale - C, D, E, G, A
2. **Channel 2 (Solar Sine Wave)**: Minor pentatonic scale - C, Eb, F, G, Bb
3. **Channel 3 (Sunrise/Sunset Events)**: Harmonic minor scale - C, D, Eb, F, G, Ab, B

---

## Tips and Best Practices

1. **Always use `--use-solar` for CSV cleanup** when your data includes solar information
2. **Use `--auto-duration` for MIDI generation** when processing full datasets (months/years)
3. **Start with verbose mode (`-v`)** to understand what the scripts are doing
4. **Use appropriate tolerance values**: 15-30 minutes for precise events, 30-60 minutes for broader detection
5. **For large datasets**: Use auto-duration to maintain consistent musical density
6. **For previews**: Use fixed duration (60-300 seconds) to create quick samples
