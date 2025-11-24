# Race Analytics Engine

Professional-grade motorsports race analysis system with AI-powered insights.

![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Status: Production](https://img.shields.io/badge/status-production-brightgreen)

## Overview

A comprehensive platform for analyzing motorsports telemetry data and generating actionable insights through:

- **Race Analysis Engine** - Enriched JSON representation of race data
- **Sector Analysis** - Deep performance insights by track section (S1/S2/S3)
- **What-If Simulator** - Counterfactual scenario analysis
- **LLM Integration** - AI-powered analysis with Ollama or cloud LLMs

## Features

- 📊 **Telemetry Processing** - Load and normalize multi-source race data
- 🏁 **Event Detection** - Identify and analyze incidents, understeer, oversteer, etc.
- 📈 **Driver Metrics** - Per-lap and per-driver performance aggregation
- 🔄 **Sector Analysis** - Breakdown performance by track sections
- ⚡ **What-If Scenarios** - Simulate outcome changes with different incidents removed
- 🤖 **LLM Coaching** - Generate AI-powered coaching feedback and race analysis

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) Ollama for local LLM analysis

### Installation

1. **Clone or download the repository**
```bash
cd race-analytics
```

2. **Setup workspace (Windows PowerShell)**
```powershell
.\setup_workspace.ps1
.\venv\Scripts\activate
```

3. **Or manual setup (all platforms)**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **(Optional) Install Ollama for local LLM**
   - Download from https://ollama.ai
   - Pull a model: `ollama pull llama3.1`
   - Ollama will run on `localhost:11434`

### Basic Usage

```python
from race_engine import build_race_facts
from race_engine.sector_analysis import build_sector_analysis
from race_engine.what_if import simulate_event_removal

# Load race data
import pandas as pd

telemetry = pd.read_csv("data/processed/telemetry_clean.csv")
per_lap = pd.read_csv("data/processed/per_lap_metrics.csv")
events = pd.read_csv("data/processed/event_detection.csv")

# Build enriched race facts
race_facts = build_race_facts(
    race_name="Race 1",
    track_name="Road America",
    telemetry_clean=telemetry,
    per_lap_metrics=per_lap,
    # ... additional data sources
)

# Analyze by sector
sector_analysis = build_sector_analysis(race_facts)

# Run what-if scenario
scenario_result = simulate_event_removal(race_facts, "understeer")
```

## Project Structure

```
race-analytics/
├── src/race_engine/                 # Main analysis engine
│   ├── analysis_engine.py            # Core race data processing
│   ├── sector_analysis.py            # Track section analysis
│   ├── what_if.py                    # Scenario simulation
│   ├── llm/
│   │   └── ollama.py                # Ollama LLM integration
│   └── processing/
│       ├── lap_processing.py         # Lap-level metrics
│       ├── event_detection.py        # Incident detection
│       └── converter.py              # Data format conversion
├── scripts/
│   ├── visualization.py              # Plotting utilities
│   └── generate_race_facts.py        # Data pipeline script
├── data/
│   ├── raw/                          # Original race files
│   │   ├── telemetry/
│   │   ├── results/
│   │   ├── sectors/
│   │   └── weather/
│   ├── processed/                    # Normalized CSV files
│   └── output/                       # Analysis results
├── examples_complete_workflow.py      # End-to-end example
├── race_analytics_pipeline.py         # Main pipeline script
├── race_llm_analyzer.py              # LLM integration script
├── llm_prompt_templates.py           # LLM prompt patterns
└── requirements.txt
```

## Core Modules

### Analysis Engine (`analysis_engine.py`)

Builds enriched race data JSON with driver, event, and lap information.

**Key Functions:**
```python
build_race_facts(
    race_name: str,
    track_name: str,
    telemetry_clean: pd.DataFrame,
    per_lap_metrics: pd.DataFrame,
    per_driver_metrics: pd.DataFrame,
    event_detection: pd.DataFrame,
    # ... optional data sources
) -> Dict[str, Any]
```

**Output Structure:**
```json
{
    "race": {"name": "Race 1", "track": "Road America"},
    "drivers": [
        {
            "vehicle_id": "GR86-001-1",
            "finish_position": 1,
            "driver_metrics": {...},
            "sector_insights": {...},
            "driver_key_events": [...]
        }
    ],
    "race_key_events": [...],
    "lap_times": [...]
}
```

### Sector Analysis (`sector_analysis.py`)

Analyzes performance by track section (S1, S2, S3, etc).

**Key Functions:**
```python
build_sector_analysis(race_facts: Dict) -> Dict[str, Any]
```

**Metrics:**
- Sector times (best, average, slowest)
- Speed characteristics
- Incident breakdown by sector
- Consistency patterns

### What-If Simulator (`what_if.py`)

Generates counterfactual scenarios by removing specific events.

**Key Functions:**
```python
simulate_no_events(race_facts: Dict) -> Dict[str, Any]
simulate_event_removal_by_role(race_facts: Dict, role: str) -> Dict[str, Any]
compare_scenarios(base: Dict, scenario: Dict) -> Dict[str, Any]
```

### LLM Integration

Generate AI-powered analysis using local Ollama or cloud LLMs.

**Prompt Patterns:**
```python
from llm_prompt_templates import (
    create_postrace_analysis_prompt,
    create_driver_comparison_prompt,
    create_coaching_feedback_prompt,
    create_whatif_analysis_prompt
)

# Generate prompt for LLM
prompt = create_postrace_analysis_prompt(race_facts)

# Send to Ollama or OpenAI
response = query_ollama(prompt, model="llama3.1")
# or
response = openai.ChatCompletion.create(model="gpt-4", messages=[...])
```

## Data Format

### Input: Raw Race Data

**Expected CSV files in `data/raw/`:**

- **telemetry/** - High-frequency telemetry (speed, acceleration, braking)
- **results/** - Race results and classifications
- **sectors/** - Sector timing information
- **weather/** - Weather conditions during race
- **best_laps/** - Best lap data by driver

### Processing: Normalized Data

**Generated CSV files in `data/processed/`:**

- `telemetry_clean.csv` - Normalized telemetry
- `per_lap_metrics.csv` - Per-lap aggregated metrics
- `per_driver_metrics.csv` - Per-driver statistics
- `event_detection.csv` - Detected incidents
- `laps_summary.csv` - Lap summary data

### Output: Analysis Results

**Generated JSON files in `data/output/`:**

- `race_facts_complete.json` - Enriched race data (primary output)
- `sector_analysis_results.json` - Sector breakdown
- `what_if_scenarios.json` - Scenario simulations
- `race_llm_analysis_results.json` - AI-powered analysis

## Examples

### 1. Run Complete Analysis Pipeline

```bash
python race_analytics_pipeline.py data/processed data/output
```

**Output:**
- race_facts_complete.json
- Comprehensive analysis report

### 2. Execute All Systems End-to-End

```bash
python examples_complete_workflow.py data/processed data/output
```

**Includes:**
- Analysis engine results
- Sector analysis
- What-if scenarios

### 3. AI-Powered Analysis with Ollama

```bash
# Make sure Ollama is running
ollama serve

# In another terminal:
python race_llm_analyzer.py
```

**Generates 4 LLM analyses:**
1. Post-race summary
2. Driver comparison
3. Coaching feedback
4. What-if scenario impact

**Output:** `data/output/race_llm_analysis_results.json`

## Configuration

### Ollama Integration

Edit `race_llm_analyzer.py` to configure:

```python
OLLAMA_URL = "http://localhost:11434"  # Ollama endpoint
MODEL = "llama3.1"                     # Model name
TEMPERATURE = 0.7                      # LLM temperature
TIMEOUT = 120                          # Request timeout (seconds)
```

### Data Paths

Default paths (can be customized):
```python
data_dir = "data/processed"   # Input processed CSV files
output_dir = "data/output"    # Output JSON files
```

## Performance

- **Analysis Speed**: 2-4 seconds for ~200 lap records
- **Memory**: ~100-200 MB for typical race (1M+ telemetry points)
- **LLM Response Time**: 30-90 seconds per analysis (depending on model)

## API Reference

### build_race_facts()

```python
def build_race_facts(
    race_name: str,
    track_name: str,
    telemetry_clean: pd.DataFrame,
    per_lap_metrics: pd.DataFrame,
    per_driver_metrics: pd.DataFrame,
    event_detection: pd.DataFrame,
    lap_times: pd.DataFrame,
    results_df: pd.DataFrame,
    class_results_df: Optional[pd.DataFrame] = None,
    sector_df: Optional[pd.DataFrame] = None,
    weather_df: Optional[pd.DataFrame] = None,
    best10_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]
```

**Returns:** Enriched race data dictionary

### build_sector_analysis()

```python
def build_sector_analysis(
    race_facts: Dict[str, Any],
    sector_names: List[str] = ["S1", "S2", "S3"]
) -> Dict[str, Any]
```

**Returns:** Sector-level analysis with performance breakdown

### query_ollama()

```python
def query_ollama(
    prompt: str,
    model: str = "llama3.1",
    temperature: float = 0.7,
    timeout: int = 120
) -> Tuple[str, int]
```

**Returns:** (response_text, token_count)

## Requirements

See `requirements.txt` for full list:

- pandas >= 1.3.0
- numpy >= 1.21.0
- requests >= 2.26.0 (for LLM APIs)
- matplotlib >= 3.4.0 (optional, for visualization)

## Testing

```bash
# Run unit tests
python -m pytest tests/

# Run specific module tests
python -m pytest tests/test_analysis_engine.py -v

# With coverage
python -m pytest --cov=src tests/
```

## Troubleshooting

### "Ollama connection refused"
- Ensure Ollama is running: `ollama serve`
- Check endpoint: http://localhost:11434 (or configured URL)
- Verify model is pulled: `ollama list`

### "pandas not found"
```bash
pip install pandas numpy
```

### "Module not found: race_engine"
```bash
# Ensure you're in the project root directory
python -m examples_complete_workflow.py
# or add to sys.path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### LLM responses taking too long
- Increase timeout in `race_llm_analyzer.py`
- Use faster model: `ollama pull mistral` (faster than llama3.1)
- Reduce prompt length by filtering data

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/analysis-improvement`)
3. Make changes with clear commit messages
4. Add tests for new functionality
5. Submit pull request

## License

MIT License - see LICENSE file for details

## Citation

If you use this system in research or publications, please cite:

```bibtex
@software{race_analytics_2024,
  title={Race Analytics Engine},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/race-analytics}
}
```

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review examples in `examples_complete_workflow.py`

## Roadmap

- [ ] Live telemetry streaming support
- [ ] Real-time incident detection
- [ ] Multi-race championship analysis
- [ ] Advanced visualization dashboard
- [ ] Cloud LLM integration (GPT-4, Claude)
- [ ] Docker containerization
- [ ] REST API server

---

**Made with ❤️ for motorsports enthusiasts and engineers.**
