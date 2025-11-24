import requests
import json
import sys
from pathlib import Path
import sys

OLLAMA_BASE = "http://localhost:11434"


user_prompt = """You are RaceAI — an expert motorsport analyst, telemetry interpreter, and race strategist.
You turn raw telemetry and event logs into clear English insights.

You always follow these rules:
- Use the provided JSON data strictly (drivers, laps, events, metrics).
- NEVER invent numbers not present in the data.
- You CAN describe positive/negative changes (e.g., “higher”, “slower”, “more stable”).
- Keep explanations technically correct but very easy to understand.
- Use racing physics: braking load, tire scrub, lateral G, traction, exit speed, etc.

You produce 3 modules based on user instruction:

================================================================
### MODULE A — POST-RACE ANALYSIS (STRUCTURED)
================================================================
When asked “generate post-race analysis” or similar, produce:

1. **Race Summary**
   - What type of race it was
   - Pace trends
   - Any defining race moment (use race_key_events)

2. **Driver Comparison Table (English, not tabular)**
   - Who was fastest overall
   - Who had the smoothest throttle
   - Who had aggressive braking
   - Who had high steering variance
   - Who showed consistent lap times

3. **Key Events Breakdown**
   For every key event:
   - What happened?
   - Why it happened (physics-based cause)
   - How much time was lost
   - Consequence for the driver

4. **Top 3 Improvement Areas**
   For each driver:
   - driving habits
   - their biggest mistake
   - their biggest opportunity to gain time

================================================================
### MODULE B — DRIVER TRAINING INSIGHTS
================================================================
When asked for driver coaching insights:
Provide:
- Steering behaviour analysis
- Throttle smoothness implications
- Braking profile explanation (aggressive vs stable)
- Where they lose most time
- How to improve on THIS circuit specifically

Use ONLY patterns visible in the JSON.

================================================================
### MODULE C — RACE STORY GENERATOR
================================================================
When asked for a “race story”, write:
- 6–12 sentences
- Exciting human-like commentary
- Mention major moments (use race_key_events)
- Build a narrative tension (“lap 4 became the turning point…”)

No numbers unless present in JSON.

================================================================
### MODULE D — WHAT-IF SCENARIO ENGINE
================================================================
When user writes ANY hypothetical situation (e.g., “What if driver braked later?”, “What if understeer didn’t happen?”, “What if they entered Turn 5 faster?”):

Output:

### What-If Scenario Result
(2–4 sentences explaining likely outcome: faster/slower, more stable/less stable, risk increased/decreased.)

### Reasoning
Explain:
- car balance
- tire load
- braking force
- lateral G
- exit speed
- driver style tags

NEVER add numbers unless in provided data.

### Risk / Reward Summary
Short bullets:
- higher/lower pace
- increased/decreased risk

================================================================

If the user asks something unclear, ask for a scenario or which module to use.
You NEVER guess the intent."""

def load_race_json(path=None):
    base = Path(__file__).parent
    if path is None:
        path = base / 'race_facts_RoadAmerica_R1_2025-08-14.json'
    else:
        path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Race facts JSON not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_ollama_server():
    try:
        resp = requests.get(f"{OLLAMA_BASE}/api/models", timeout=2)
        if resp.status_code == 200:
            return True, None
        return False, f"Unexpected status {resp.status_code} from {OLLAMA_BASE}/api/models"
    except requests.exceptions.RequestException as e:
        return False, str(e)


def call_ollama(prompt, model="llama3.1:latest"):
    try:
        resp = requests.post(f"{OLLAMA_BASE}/api/generate", json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }, timeout=10)
        resp.raise_for_status()
        # Prefer parsed JSON, but fall back to raw text if not JSON
        try:
            return resp.json()
        except ValueError:
            return {"response": resp.text}
    except requests.exceptions.HTTPError as e:
        raise
    except requests.exceptions.RequestException as e:
        raise


def local_analyze(race_json):
    # Fallback local MODULE A analysis using only data present in race_json.
    out = {
        "race_summary": {},
        "driver_comparison": [],
        "key_events_breakdown": [],
        "top_improvements": {}
    }

    race = race_json.get("race", {})
    out["race_summary"]["event_name"] = race.get("event_name")
    out["race_summary"]["track"] = race.get("track")
    out["race_summary"]["total_laps"] = race.get("total_laps")

    # gather driver metrics if available
    drivers = race_json.get("drivers", [])
    # helper safe getters
    fastest = None
    smoothest_throttle = None
    aggressive_braker = None
    high_steering_var = None
    most_consistent = None

    for d in drivers:
        vid = d.get("vehicle_id") or d.get("vehicle_number") or "<unknown>"
        dm = d.get("driver_metrics", {})
        # fastest by lap_time_best (lower is faster)
        lt_best = dm.get("lap_time_best")
        if isinstance(lt_best, (int, float)):
            if fastest is None or lt_best < fastest[1]:
                fastest = (vid, lt_best)
        # smoothest throttle by throttle_smoothness_mean (lower = smoother)
        thr = dm.get("throttle_smoothness_mean")
        if isinstance(thr, (int, float)):
            if smoothest_throttle is None or thr < smoothest_throttle[1]:
                smoothest_throttle = (vid, thr)
        # aggressive braking by brake_spikes_sum (higher = aggressive)
        bs = dm.get("brake_spikes_sum")
        if isinstance(bs, (int, float)):
            if aggressive_braker is None or bs > aggressive_braker[1]:
                aggressive_braker = (vid, bs)
        # high steering variance
        sv = dm.get("steering_variance_mean")
        if isinstance(sv, (int, float)):
            if high_steering_var is None or sv > high_steering_var[1]:
                high_steering_var = (vid, sv)
        # most consistent by lap_time_std (lower = consistent)
        lts = dm.get("lap_time_std")
        if isinstance(lts, (int, float)):
            if most_consistent is None or lts < most_consistent[1]:
                most_consistent = (vid, lts)

    # build short english comparison lines (only using available fields)
    if fastest:
        out["driver_comparison"].append(f"Fastest best lap: {fastest[0]}")
    if smoothest_throttle:
        out["driver_comparison"].append(f"Smoothest throttle: {smoothest_throttle[0]}")
    if aggressive_braker:
        out["driver_comparison"].append(f"Most brake spikes: {aggressive_braker[0]}")
    if high_steering_var:
        out["driver_comparison"].append(f"Highest steering variance: {high_steering_var[0]}")
    if most_consistent:
        out["driver_comparison"].append(f"Most consistent (lowest lap std): {most_consistent[0]}")

    # key events (echo back)
    for ev in race_json.get("race_key_events", []):
        ev_summary = {
            "vehicle_id": ev.get("vehicle_id"),
            "lap": ev.get("lap"),
            "event_type": ev.get("event_type"),
            "severity": ev.get("severity"),
            "time_loss": ev.get("time_loss"),
            "description": ev.get("description")
        }
        out["key_events_breakdown"].append(ev_summary)

    # top improvements per driver: simple mapping from tags and events
    for d in drivers:
        vid = d.get("vehicle_id") or "<unknown>"
        tags = d.get("driver_style_tags", [])
        improvements = []
        if "erratic_steering" in tags:
            improvements.append("Smooth steering inputs; reduce abrupt corrections.")
        if "aggressive_braking" in tags:
            improvements.append("Brake modulation to avoid lockups and reduce time loss.")
        if "smooth_steering" in tags:
            improvements.append("Leverage smooth steering to improve exit speed.")
        # fallback if none
        if not improvements:
            improvements.append("Review tyre warm-up and corner exits for marginal gains.")
        out["top_improvements"][vid] = {
            "suggestions": improvements,
            "biggest_visible_issue": d.get("driver_key_events", [])[:1]  # first event if any
        }

    return out


def generate_post_race_analysis(race_json, module='A'):
    ok, err = check_ollama_server()
    if ok:
        instruction = """
Please produce MODULE A — POST-RACE ANALYSIS (STRUCTURED) using ONLY the provided JSON data.
Follow the RULES in the system prompt. Do not invent numbers. Be concise and technical.
Return JSON with sections: race_summary, driver_comparison, key_events_breakdown, top_improvements.
"""
        full_prompt = user_prompt + "\n\n" + instruction + "\nRACE_JSON:\n" + json.dumps(race_json, indent=2)
        try:
            resp = call_ollama(full_prompt)
            # resp expected to be a dict possibly with a string field 'response'
            if isinstance(resp, dict):
                text = resp.get('response') or resp.get('output') or None
                if text:
                    # try to parse model output as JSON
                    try:
                        parsed = json.loads(text)
                        return parsed
                    except Exception:
                        # not JSON — return as a wrapped text field
                        return {"remote_response_text": text}
                # no 'response' field — return the dict directly
                return resp
            # unexpected type — stringify
            return {"remote_response": str(resp)}
        except requests.exceptions.HTTPError as e:
            # server returned 4xx/5xx - fallback to local
            print("Remote Ollama returned error:", e, file=sys.stderr)
            return local_analyze(race_json)
        except Exception as e:
            print("Error calling remote Ollama:", e, file=sys.stderr)
            return local_analyze(race_json)
    else:
        print(f"Ollama server unreachable: {err}. Using local analyzer.", file=sys.stderr)
        return local_analyze(race_json)


def find_event(race_json, vehicle_id, lap):
    # search race_key_events and drivers' events
    lap = int(lap)
    for ev in race_json.get('race_key_events', []):
        if ev.get('vehicle_id') == vehicle_id and int(ev.get('lap', -1)) == lap:
            return ev
    # search per-driver events
    for d in race_json.get('drivers', []):
        if d.get('vehicle_id') == vehicle_id:
            for ev in d.get('driver_key_events', []):
                if int(ev.get('lap', -1)) == lap:
                    return ev
    return None


def format_whatif_prompt(event, race_json):
    # Build strict instruction telling the LLM to output exactly the 3 sections
    template = (
        "You are RaceAI. Produce ONLY the following sections (no extra text):\n"
        "\nWhat-If Scenario Result\n\n{RESULT}\n\nReasoning\n\n{REASONING}\n\nRisk / Reward Summary\n\n{RISK}\n"
    )
    # Provide the event JSON and a short template example (user-provided)
    example = (
        "Example output format:\n\n"
        "What-If Scenario Result\n\nIf GR86-026-72 avoided the Lap 4 understeer, they would likely have retained more speed...\n\n"
    )
    full = (
        "Use ONLY the data provided in the JSON below. NEVER invent numbers not in the data.\n"
        "Event JSON:\n" + json.dumps(event, indent=2) + "\n\n"
        "Race JSON keys available: race, drivers, race_key_events, lap_times.\n\n"
        "Produce the output using the exact section headings and structure. Keep it concise.\n"
        "Respond with plain text exactly matching the requested sections.\n\n"
        + example
    )
    return full


def local_whatif_text(event):
    # Construct the three sections using only fields in event
    ev = event
    vid = ev.get('vehicle_id')
    lap = ev.get('lap')
    ev_type = ev.get('event_type')
    severity = ev.get('severity')
    time_loss = ev.get('time_loss')
    metrics = ev.get('metrics', {})
    steering = metrics.get('steering_correction_deg')
    speed_loss = metrics.get('speed_loss_kph')

    result = (
        f"If {vid} avoided the Lap {lap} {ev_type}, they would likely have retained more speed through the corner and recovered a large portion of the measured time loss (the event shows a time_loss of {time_loss}). "
        "That improved mid-corner stability would increase exit speed onto the following straight and likely translate to a faster lap for that lap."
    )

    reasoning = (
        f"Measured event facts: the Lap {lap} event for {vid} is a {ev_type} with a steering correction of {steering}° and a speed loss of {speed_loss} kph; recorded time_loss = {time_loss}. These are the direct data points used below.\n\n"
        "Physics chain: the large corrective steering indicates the front tyres were not generating the requested lateral force (understeer). The driver’s large correction and the speed drop show momentum was lost mid-corner.\n\n"
        "How avoiding it helps: without the large steering correction and speed drop there is less front‑tire scrub and lower slip angle — that preserves cornering energy and increases exit traction and speed onto the straight. Because the event’s measured time loss is the recorded value above, avoiding the understeer would recover most of that loss on the lap in question.\n\n"
        "Driver context: use driver_style_tags from the driver entry to describe fit-to-driver."
    )

    risk = (
        "Reward: recover most of the recorded time_loss on that lap; better exit speed.\n\n"
        "Risk: higher entry speed or later releases (to avoid the correction) increases risk of front lockup or exceeding tyre load; that could trade an understeer for a lockup or off-line correction if not accompanied by braking/entry adjustments."
    )

    out = (
        "What-If Scenario Result\n\n" + result + "\n\nReasoning\n\n" + reasoning + "\n\nRisk / Reward Summary\n\n" + risk
    )
    return out


def generate_whatif(vehicle_id, lap, race_json):
    event = find_event(race_json, vehicle_id, lap)
    if event is None:
        return {"error": f"Event not found for {vehicle_id} lap {lap}"}

    # try remote first
    ok, err = check_ollama_server()
    prompt = format_whatif_prompt(event, race_json)
    if ok:
        try:
            resp = call_ollama(prompt)
            # extract text
            if isinstance(resp, dict):
                text = resp.get('response') or resp.get('output') or None
                if text:
                    return {"remote_response_text": text}
            return {"remote_response": str(resp)}
        except Exception as e:
            print('Remote error, falling back to local what-if:', e, file=sys.stderr)
    # fallback
    return {"local_whatif": local_whatif_text(event)}


if __name__ == '__main__':
    try:
        race = load_race_json()
    except Exception as e:
        print('Error loading race JSON:', e, file=sys.stderr)
        sys.exit(1)
    # CLI: support `whatif <vehicle_id> <lap>` and default to post-race analysis
    argv = sys.argv[1:]
    if len(argv) >= 1 and argv[0].lower() == 'whatif':
        if len(argv) < 3:
            print('Usage: python ollama.py whatif <vehicle_id> <lap>', file=sys.stderr)
            sys.exit(2)
        vehicle_id = argv[1]
        lap = argv[2]
        out = generate_whatif(vehicle_id, lap, race)
        # prefer printing text if present
        if 'local_whatif' in out:
            print(out['local_whatif'])
        elif 'remote_response_text' in out:
            print(out['remote_response_text'])
        else:
            print(json.dumps(out, indent=2))
    else:
        result = generate_post_race_analysis(race)
        # print structured JSON output
        print(json.dumps(result, indent=2))


