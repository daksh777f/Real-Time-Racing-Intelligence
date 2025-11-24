"""
LLM Prompt Templates - Race Analysis Prompt Patterns

Provides reusable prompt templates for LLM integration with race data:
    1. Post-Race Analysis - Full race_facts JSON analysis
    2. What-If Scenarios - Small payload counterfactual analysis
    3. Driver Comparison - Head-to-head driver analysis
    4. Coaching Feedback - Personalized driver coaching
    5. Agentic Workflows - Multi-turn reasoning patterns

Compatible with OpenAI, Claude, Ollama, and other LLMs.

Usage:
    from llm_prompt_templates import create_postrace_analysis_prompt
    
    race_facts = {...}  # from race_engine
    prompt = create_postrace_analysis_prompt(race_facts)
    # Send prompt to LLM API
"""

import json
from typing import Dict, Any


# ============================================================================
# PATTERN 1: POST-RACE ANALYSIS
# ============================================================================

def create_postrace_analysis_prompt(race_facts: Dict[str, Any]) -> str:
    """
    Full race_facts JSON sent to LLM for comprehensive post-race analysis.
    
    Usage:
        race_facts = build_race_facts(...)
        prompt = create_postrace_analysis_prompt(race_facts)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
    """
    prompt = f"""You are an expert motorsports analyst. Analyze this race telemetry and provide detailed insights.

ENRICHED RACE DATA:
{json.dumps(race_facts, indent=2)}

Please provide analysis on these dimensions:

1. **Race Winner & Top Performers**
   - Who won and why?
   - Top 3 drivers and their strengths
   - Consistency vs peak performance tradeoffs

2. **Driver Performance by Sector**
   - Which drivers dominated which sectors?
   - Who struggled in specific corners?
   - Evidence of track-specific strengths (S1 braking, S2 speed, S3 exits)

3. **Critical Race Events**
   - Which incidents shaped the final outcome?
   - Were there "race turning points"?
   - How much time did top incidents cost each driver?

4. **Driving Style Profiles**
   - Aggressive vs smooth drivers
   - Braking intensity patterns
   - Steering smoothness and confidence

5. **Weather Impact**
   - How did weather affect tire/brake performance?
   - Did any drivers adapt better than others?
   - Temperature variations and their effects

6. **Strategic Recommendations**
   - What should each top-5 finisher do differently next race?
   - Which drivers have untapped potential?
   - How close was the competition?

Provide specific data references and quantifiable insights."""
    
    return prompt


# ============================================================================
# PATTERN 2: WHAT-IF SCENARIOS
# ============================================================================

def create_whatif_analysis_prompt(what_if_payload: Dict[str, Any]) -> str:
    """
    Focused what-if payload for scenario-based LLM analysis.
    
    Usage:
        payload = build_what_if_payload(driver_id, scenario, orig, adj)
        prompt = create_whatif_analysis_prompt(payload)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": WHATIF_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
    """
    prompt = f"""
What-If Scenario Analysis:

{json.dumps(what_if_payload, indent=2)}

Please analyze this scenario and answer:

1. **Result Impact**: How does this change the driver's race result?
   - Time gain: {what_if_payload['time_gain_seconds']:.1f}s
   - Position change: {what_if_payload.get('position_change', 'TBD')}
   - Realistic improvement? (explain)

2. **Psychological & Strategic Implications**:
   - How would this impact driver morale/confidence?
   - Strategic decisions that might have been different?
   - Championship implications?

3. **Achievability Assessment**:
   - Was this driver realistically capable of this result?
   - What would need to change (driving style, car setup, conditions)?
   - Evidence from their peak performance moments?

4. **Counterfactual Learning**:
   - What can this driver learn from the scenario?
   - Which aspects of their driving should they focus on?
   - Specific techniques or strategies to improve?

Keep your response concise and data-driven."""
    
    return prompt


WHATIF_SYSTEM_PROMPT = """You are the Race Strategy Scenario AI - an expert at analyzing what-if scenarios in motorsports.

Your role:
- Evaluate how specific incident removals would change race outcomes
- Consider driver psychology and strategic decision-making
- Ground assessments in realistic driving capabilities
- Provide actionable insights for driver coaching

Always:
- Reference specific times and positions from the payload
- Consider realistic vs unrealistic scenarios
- Acknowledge limitations in the data
- Suggest next steps for improvement"""


# ============================================================================
# PATTERN 3: DRIVER COMPARISON
# ============================================================================

def create_driver_comparison_prompt(
    race_facts: Dict[str, Any],
    driver_ids: list,
) -> str:
    """
    Compare specific drivers across multiple dimensions.
    
    Usage:
        prompt = create_driver_comparison_prompt(race_facts, ["GR86-026-72", "GR86-004-78"])
        response = llm.generate(prompt)
    """
    # Extract driver data
    drivers_data = {
        d['vehicle_id']: d for d in race_facts['drivers']
        if d['vehicle_id'] in driver_ids
    }
    
    prompt = f"""Compare these drivers across their race performance:

DRIVERS TO COMPARE: {', '.join(driver_ids)}

DRIVER DATA:
{json.dumps(drivers_data, indent=2)}

Please provide:

1. **Head-to-Head Comparison**
   - Who performed better overall?
   - Key differences in their approaches?

2. **Sector-by-Sector Breakdown**
   - Where did each driver excel?
   - Where did they struggle?
   - Time deltas between them?

3. **Consistency Analysis**
   - Who was more consistent?
   - Evidence from lap times and incident patterns?

4. **Incident Comparison**
   - How did incidents affect each driver?
   - Who recovered better from adversity?

5. **Coaching Feedback**
   - What can each driver learn from the other?
   - Specific techniques to adopt?
   - Areas to focus on for improvement?

Format as a structured comparison table where possible."""
    
    return prompt


# ============================================================================
# PATTERN 4: AGENTIC WORKFLOW
# ============================================================================

class RaceAnalysisAgent:
    """
    Multi-turn agentic workflow for race analysis.
    Uses Tools: get_race_facts, simulate_whatif, get_sector_details
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.tools = {
            "get_race_facts": self.get_race_facts,
            "simulate_what_if": self.simulate_what_if,
            "get_driver_details": self.get_driver_details,
            "compare_drivers": self.compare_drivers,
        }
    
    def system_prompt(self) -> str:
        return """You are an expert motorsports analysis agent. You have access to race telemetry and simulation tools.

Your capabilities:
1. get_race_facts(race_id) - Load complete race analysis JSON
2. simulate_what_if(driver_id, scenario) - What-if scenario simulation
3. get_driver_details(driver_id) - Deep dive into specific driver
4. compare_drivers(driver_ids) - Head-to-head comparison

Your workflow:
- Start by loading race_facts
- Ask clarifying questions about what the user wants to analyze
- Use tools iteratively to gather data
- Synthesize findings into clear recommendations
- Always cite data and explain your reasoning

Current available races: Road America R1 2025

User question will follow."""
    
    def execute(self, user_query: str, race_id: str = "road_america_r1_2025"):
        """Execute agentic workflow"""
        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": user_query}
        ]
        
        # Simulated multi-turn loop
        turn = 0
        max_turns = 5
        
        while turn < max_turns:
            # Get LLM response with tool use
            response = self.llm.create(
                model="gpt-4",
                messages=messages,
            )
            
            assistant_message = response.choices[0].message
            messages.append({"role": "assistant", "content": assistant_message.content})
            
            # Check if agent wants to use tools
            if "TOOL:" in assistant_message.content:
                # Parse and execute tool
                tool_call = self._parse_tool_call(assistant_message.content)
                tool_result = self._execute_tool(tool_call, race_id)
                
                messages.append({"role": "user", "content": f"Tool result: {tool_result}"})
                turn += 1
            else:
                # Agent produced final answer
                return assistant_message.content
        
        return "Max turns reached"
    
    def _parse_tool_call(self, content: str) -> Dict[str, Any]:
        """Parse tool call from LLM output"""
        import re
        match = re.search(r"TOOL:\s*(\w+)\((.*?)\)", content)
        if match:
            return {"name": match.group(1), "args": match.group(2)}
        return {"name": "none", "args": ""}
    
    def _execute_tool(self, tool_call: Dict, race_id: str) -> str:
        """Execute requested tool"""
        tool_name = tool_call["name"]
        if tool_name in self.tools:
            return str(self.tools[tool_name](tool_call["args"], race_id))
        return "Tool not found"
    
    # Tool implementations (stubs)
    def get_race_facts(self, args: str, race_id: str) -> Dict:
        """Load race facts"""
        # In real implementation: load from cache/db
        return {"race_id": race_id, "drivers": 27, "laps": 8}
    
    def simulate_what_if(self, args: str, race_id: str) -> Dict:
        """Run what-if simulation"""
        # In real implementation: call what_if.simulate_no_events
        return {"scenario": args, "position_change": 2}
    
    def get_driver_details(self, driver_id: str, race_id: str) -> Dict:
        """Get driver profile"""
        # In real implementation: extract from race_facts
        return {"driver_id": driver_id, "position": 5}
    
    def compare_drivers(self, driver_ids: str, race_id: str) -> Dict:
        """Compare drivers"""
        # In real implementation: use comparison tools
        return {"drivers": driver_ids, "winner": driver_ids.split(",")[0]}


# ============================================================================
# PATTERN 5: COACHING FEEDBACK
# ============================================================================

def create_coaching_feedback_prompt(
    race_facts: Dict[str, Any],
    driver_id: str,
) -> str:
    """
    Personalized coaching feedback for a specific driver.
    """
    driver = next((d for d in race_facts['drivers'] if d['vehicle_id'] == driver_id), None)
    if not driver:
        return f"Driver {driver_id} not found in race_facts"
    
    prompt = f"""Generate personalized coaching feedback for this driver:

DRIVER: {driver_id}
POSITION: {driver.get('finish_pos', 'Unknown')}

PERFORMANCE DATA:
- Lap Time Mean: {driver['driver_metrics'].get('lap_time_mean', 'N/A')}
- Best Lap: {driver['driver_metrics'].get('lap_time_best', 'N/A')}
- Max Speed: {driver['driver_metrics'].get('max_speed_mean', 'N/A')} kph
- Peak Lateral G: {driver['driver_metrics'].get('peak_lat_G_mean', 'N/A')}
- Steering Variance: {driver['driver_metrics'].get('steering_variance_mean', 'N/A')}

DRIVING STYLE:
{driver['driver_style_tags']}

INCIDENTS:
{json.dumps(driver['driver_key_events'][:3], indent=2)}

SECTOR PERFORMANCE:
{json.dumps(driver.get('sector_insights', {}), indent=2)}

Please provide coaching feedback on:

1. **What You Did Well** (2-3 specific examples)
   - Reference actual incidents or sector performances
   - Be encouraging and specific

2. **Areas for Improvement** (3-5 items)
   - Data-backed observations
   - Specific techniques to work on
   - How to avoid repeated mistakes

3. **Next Race Focus**
   - Top 3 priorities
   - Realistic goals
   - How to leverage your strengths

4. **Comparative Insights**
   - How did you compare to winners?
   - What can you learn from top performers?

Keep it motivating but honest. Reference specific data points."""
    
    return prompt


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Example: Create different prompts from a race_facts JSON
    
    # 1. Post-race analysis
    print("=" * 70)
    print("EXAMPLE 1: POST-RACE ANALYSIS PROMPT")
    print("=" * 70)
    
    sample_race_facts = {
        "race": {"event_name": "Road America R1", "track": "Road America", "total_laps": 8},
        "drivers": [
            {
                "vehicle_id": "GR86-026-72",
                "finish_pos": 5,
                "driver_metrics": {"lap_time_mean": 162.5},
                "driver_key_events": [],
                "sector_insights": {},
            }
        ],
        "race_key_events": [],
    }
    
    # prompt = create_postrace_analysis_prompt(sample_race_facts)
    # print(prompt[:500] + "...")
    
    # 2. What-if scenario
    print("\n" + "=" * 70)
    print("EXAMPLE 2: WHAT-IF SCENARIO PROMPT")
    print("=" * 70)
    
    sample_payload = {
        "scenario": "Remove Lap 4 understeer turning point",
        "driver_id": "GR86-026-72",
        "original_time_seconds": 1234.5,
        "adjusted_time_seconds": 1210.3,
        "time_gain_seconds": 24.2,
        "time_gain_percent": 1.96,
        "original_position": 7,
        "adjusted_position": 5,
        "position_change": 2,
        "result_improvement": "improved",
    }
    
    prompt = create_whatif_analysis_prompt(sample_payload)
    print(prompt)
