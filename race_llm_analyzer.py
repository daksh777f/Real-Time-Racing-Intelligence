#!/usr/bin/env python3
"""
Race LLM Analyzer - AI-Powered Race Analysis

Real-time AI-powered race analysis using local Ollama LLMs.
Generates post-race summaries, driver comparisons, coaching feedback, 
and what-if scenario analysis.

Models: llama3.1 (8B), gpt-oss:20b, or any Ollama-compatible model.
API: HTTP to Ollama instance at localhost:11434 (configurable).

Usage:
    python race_llm_analyzer.py
    
Example:
    Loads race_facts_complete.json from data/output/
    Runs 4 sequential LLM analyses
    Saves results to data/output/race_llm_analysis_results.json
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
import requests

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd
from race_engine import build_race_facts
from llm_prompt_templates import (
    create_postrace_analysis_prompt,
    create_whatif_analysis_prompt,
    create_driver_comparison_prompt,
    create_coaching_feedback_prompt
)


# ============================================================================
# OLLAMA INTEGRATION
# ============================================================================

def query_ollama(prompt, model="llama3.1", temperature=0.7, max_tokens=1024):
    """Query Ollama with race analysis prompt."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": temperature,
                "num_ctx": 4096,
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', ''), result.get('eval_count', 0)
        else:
            return None, 0
    except requests.exceptions.Timeout:
        print(f"  ⏱ Timeout - response may have been too long")
        return None, 0
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None, 0


# ============================================================================
# LOAD DATA AND GENERATE PROMPTS
# ============================================================================

def load_and_prepare_data():
    """Load race data and prepare for LLM analysis."""
    print("\n" + "="*80)
    print("LOADING RACE DATA")
    print("="*80)
    
    base_dir = Path(__file__).parent
    processed_dir = base_dir / "data" / "processed"
    
    # Load existing race facts
    race_facts_file = base_dir / "data" / "output" / "race_facts_complete.json"
    
    if race_facts_file.exists():
        print(f"✓ Loading pre-built race_facts from {race_facts_file.name}")
        with open(race_facts_file, 'r') as f:
            race_facts = json.load(f)
        
        print(f"  - Drivers: {len(race_facts.get('drivers', []))}")
        print(f"  - Events: {len(race_facts.get('race_key_events', []))}")
        print(f"  - Laps: {len(race_facts.get('lap_times', []))}")
        return race_facts
    else:
        print(f"✗ race_facts_complete.json not found")
        return None


# ============================================================================
# LLM ANALYSIS EXECUTION
# ============================================================================

def run_ollama_analysis(race_facts):
    """Run complete LLM analysis using Ollama."""
    
    print("\n" + "="*80)
    print("OLLAMA-POWERED ANALYSIS")
    print("="*80)
    
    results = {}
    
    # Check Ollama status
    print("\n🔍 Checking Ollama...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = response.json().get('models', [])
        model_names = [m['name'] for m in models]
        print(f"✓ Ollama running with {len(models)} models:")
        for name in model_names[:3]:
            print(f"  • {name}")
    except Exception as e:
        print(f"✗ Ollama not accessible: {e}")
        return None
    
    # Use the best available model
    model = "llama3.1" if any("llama3" in m for m in model_names) else model_names[0]
    print(f"\n🤖 Using model: {model}")
    
    # ========================================================================
    # ANALYSIS 1: POST-RACE SUMMARY
    # ========================================================================
    
    print("\n" + "-"*80)
    print("ANALYSIS 1: POST-RACE SUMMARY")
    print("-"*80)
    
    prompt = create_postrace_analysis_prompt(race_facts)
    print(f"Prompt length: {len(prompt)} chars")
    print("🔄 Querying Ollama (this will take 30-60 seconds)...\n")
    
    start_time = time.time()
    response, token_count = query_ollama(prompt, model=model, max_tokens=1500)
    elapsed = time.time() - start_time
    
    if response:
        print("✓ OLLAMA RESPONSE:")
        print("-"*80)
        print(response)
        print("-"*80)
        print(f"Time: {elapsed:.1f}s | Tokens: {token_count}")
        results['post_race_summary'] = response
    else:
        print("✗ Failed to get response from Ollama")
    
    # ========================================================================
    # ANALYSIS 2: SECTOR PERFORMANCE INSIGHTS
    # ========================================================================
    
    print("\n" + "-"*80)
    print("ANALYSIS 2: SECTOR PERFORMANCE INSIGHTS")
    print("-"*80)
    
    # Get driver IDs
    drivers = race_facts.get('drivers', [])
    driver_ids = [d.get('vehicle_id', 'Unknown') for d in drivers[:2]] if drivers else []
    
    if driver_ids:
        prompt = create_driver_comparison_prompt(race_facts, driver_ids)
        print(f"Comparing: {', '.join(driver_ids)}")
        print(f"Prompt length: {len(prompt)} chars")
        print("🔄 Querying Ollama...\n")
        
        start_time = time.time()
        response, token_count = query_ollama(prompt, model=model, max_tokens=1500)
        elapsed = time.time() - start_time
        
        if response:
            print("✓ OLLAMA RESPONSE:")
            print("-"*80)
            print(response)
            print("-"*80)
            print(f"Time: {elapsed:.1f}s | Tokens: {token_count}")
            results['driver_comparison'] = response
        else:
            print("✗ Failed to get response from Ollama")
    else:
        print("✗ No drivers found for comparison")
    
    # ========================================================================
    # ANALYSIS 3: TOP DRIVER COACHING
    # ========================================================================
    
    print("\n" + "-"*80)
    print("ANALYSIS 3: TOP DRIVER COACHING FEEDBACK")
    print("-"*80)
    
    # Get top driver
    drivers = race_facts.get('drivers', [])
    if drivers:
        top_driver = drivers[0]
        driver_id = top_driver.get('vehicle_id', 'Unknown')
        
        prompt = create_coaching_feedback_prompt(race_facts, driver_id)
        print(f"Driver: {driver_id}")
        print(f"Prompt length: {len(prompt)} chars")
        print("🔄 Querying Ollama...\n")
        
        start_time = time.time()
        response, token_count = query_ollama(prompt, model=model, max_tokens=1500)
        elapsed = time.time() - start_time
        
        if response:
            print("✓ OLLAMA RESPONSE:")
            print("-"*80)
            print(response)
            print("-"*80)
            print(f"Time: {elapsed:.1f}s | Tokens: {token_count}")
            results[f'coaching_{driver_id}'] = response
        else:
            print("✗ Failed to get response from Ollama")
    
    # ========================================================================
    # ANALYSIS 4: WHAT-IF SCENARIO
    # ========================================================================
    
    print("\n" + "-"*80)
    print("ANALYSIS 4: WHAT-IF SCENARIO ANALYSIS")
    print("-"*80)
    
    # Create a what-if scenario
    whatif_scenario = {
        "scenario": "Remove all understeer incidents",
        "driver_id": driver_id if drivers else "All",
        "original_time_seconds": 2039.3,
        "adjusted_time_seconds": 2036.6,
        "time_gain_seconds": 2.7,
        "position_change": 0
    }
    
    prompt = create_whatif_analysis_prompt(whatif_scenario)
    print(f"Scenario: {whatif_scenario['scenario']}")
    print(f"Prompt length: {len(prompt)} chars")
    print("🔄 Querying Ollama...\n")
    
    start_time = time.time()
    response, token_count = query_ollama(prompt, model=model, max_tokens=1500)
    elapsed = time.time() - start_time
    
    if response:
        print("✓ OLLAMA RESPONSE:")
        print("-"*80)
        print(response)
        print("-"*80)
        print(f"Time: {elapsed:.1f}s | Tokens: {token_count}")
        results['whatif_scenario'] = response
    else:
        print("✗ Failed to get response from Ollama")
    
    return results


# ============================================================================
# SAVE RESULTS
# ============================================================================

def save_results(race_facts, llm_responses):
    """Save LLM responses to files."""
    
    print("\n" + "="*80)
    print("SAVING RESULTS")
    print("="*80)
    
    output_dir = Path(__file__).parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    output_file = output_dir / "ollama_analysis_results.json"
    results = {
        "timestamp": datetime.now().isoformat(),
        "race_facts": race_facts,
        "llm_responses": llm_responses,
        "model_used": "llama3.1"
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"✓ Saved JSON results: {output_file}")
    print(f"  Size: {output_file.stat().st_size / 1024:.1f} KB")
    
    # Save as readable text
    text_file = output_dir / "ollama_analysis_results.txt"
    with open(text_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("OLLAMA-POWERED RACE ANALYSIS RESULTS\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Model: llama3.1\n\n")
        
        f.write("RACE OVERVIEW:\n")
        f.write("-"*80 + "\n")
        f.write(f"Track: {race_facts.get('race', {}).get('track', 'N/A')}\n")
        f.write(f"Drivers: {len(race_facts.get('drivers', []))}\n")
        f.write(f"Events: {len(race_facts.get('race_key_events', []))}\n\n")
        
        for key, response in llm_responses.items():
            f.write("\n" + "="*80 + "\n")
            f.write(f"{key.upper().replace('_', ' ')}\n")
            f.write("="*80 + "\n")
            f.write(response + "\n")
    
    print(f"✓ Saved text results: {text_file}")
    print(f"  Size: {text_file.stat().st_size / 1024:.1f} KB")
    
    return output_file, text_file


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution."""
    print("\n")
    print("+"+ "="*78 + "+")
    print("|" + "OLLAMA-POWERED LLM INTEGRATION FOR RACE ANALYSIS".center(78) + "|")
    print("|" + "Real AI-powered coaching, analysis, and insights".center(78) + "|")
    print("+"+ "="*78 + "+")
    
    try:
        # Load race data
        race_facts = load_and_prepare_data()
        if not race_facts:
            print("\n✗ Could not load race facts. Run final_llm_integration.py first.")
            return
        
        # Run Ollama analysis
        llm_responses = run_ollama_analysis(race_facts)
        if not llm_responses:
            print("\n✗ Analysis failed")
            return
        
        # Save results
        json_file, text_file = save_results(race_facts, llm_responses)
        
        # Final summary
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"\n✓ Generated {len(llm_responses)} LLM responses")
        print(f"\nOutput files:")
        print(f"  • {json_file.name} - Full JSON with all data")
        print(f"  • {text_file.name} - Human-readable format")
        print(f"\nNext steps:")
        print(f"  1. Review the analysis results above")
        print(f"  2. Check output files for full responses")
        print(f"  3. Use insights for coaching and strategy")
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
