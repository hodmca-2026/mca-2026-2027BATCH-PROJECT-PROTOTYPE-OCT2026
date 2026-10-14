"""
Generate Synthetic Incident/Near-miss/Maintenance Reports

Produces 60-80 report objects matching schema 5.1 from the build spec.
Covers >=5 equipment types and all 3 report types (accident, near_miss, maintenance_log).
Uses templated string generation with randomized parameters — works with zero API keys.
"""

import json
import random
import os
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NUM_REPORTS = 70  # Target: 60-80

EQUIPMENT_TYPES = [
    "induction motor",
    "conveyor belt",
    "forklift",
    "electrical panel",
    "compressor",
    "hydraulic press",
    "welding station",
]

HAZARD_TYPES = [
    "overheating",
    "fire",
    "fall",
    "spill",
    "electrical shock",
    "mechanical failure",
    "pressure buildup",
    "chemical exposure",
    "crushing",
    "vibration damage",
]

LOCATIONS = [
    "Building 1, Line 1",
    "Building 1, Line 2",
    "Building 2, Line 1",
    "Building 2, Line 3",
    "Building 3, Line 1",
    "Building 3, Line 2",
    "Building 4, Maintenance Bay",
    "Warehouse A, Loading Dock",
    "Warehouse B, Storage Area",
    "Outdoor Yard, Section C",
]

SEVERITIES = ["low", "medium", "high", "critical"]
SEVERITY_WEIGHTS = [0.30, 0.35, 0.25, 0.10]

REPORT_TYPES = ["accident", "near_miss", "maintenance_log"]
REPORT_TYPE_WEIGHTS = [0.35, 0.35, 0.30]

# ---------------------------------------------------------------------------
# Narrative templates — organized by (equipment, hazard) combinations
# ---------------------------------------------------------------------------
NARRATIVE_TEMPLATES = {
    # Motor-related
    ("induction motor", "overheating"): [
        "During routine operation on {date}, induction motor {motor_id} in {location} was found to be running at elevated temperatures exceeding {temp}°C. The bearing temperature sensor triggered an alarm at {time}. Operators reported unusual vibration patterns approximately {hours_before} hours before the temperature spike. Maintenance crew was dispatched and discovered degraded lubrication in the drive-end bearing. The motor was shut down for emergency maintenance. Root cause analysis indicated inadequate lubrication schedule and possible overloading due to a misaligned coupling. {severity_text}",
        "Induction motor {motor_id} at {location} experienced thermal runaway on {date}. Temperature readings climbed steadily from a baseline of 62°C to {temp}°C over a {hours_before}-hour period. The winding insulation resistance test post-event showed degradation consistent with prolonged overheating. Contributing factors included blocked ventilation ducts and ambient temperature of 38°C during a heat wave. The motor was taken offline and replaced with a spare unit. {severity_text}",
        "On {date}, shift supervisor reported smoke emanating from induction motor {motor_id} in {location}. Thermal imaging confirmed surface temperature of {temp}°C, well above the rated maximum of 80°C. Emergency shutdown was initiated per protocol SOP-EM-004. Investigation revealed a seized cooling fan and accumulated dust on the motor housing restricting heat dissipation. {severity_text}",
    ],
    ("induction motor", "mechanical failure"): [
        "Induction motor {motor_id} in {location} suffered catastrophic bearing failure on {date} at approximately {time}. The motor had been in continuous service for {run_hours} hours since last scheduled maintenance. Vibration analysis data from the preceding week showed a progressive increase in amplitude at the bearing defect frequency. The outer race of the drive-end bearing was found fractured. Production on Line {line} was halted for {downtime} hours during replacement. {severity_text}",
        "On {date}, motor {motor_id} at {location} experienced a shaft coupling failure during peak production. The flexible coupling element disintegrated, causing the motor to run unloaded at elevated speed before the overload relay tripped after {seconds} seconds. The root cause was fatigue cracking in the coupling hub, exacerbated by persistent misalignment that had been noted but not corrected in the previous two maintenance inspections. {severity_text}",
    ],
    ("induction motor", "vibration damage"): [
        "Vibration monitoring on motor {motor_id} at {location} flagged an abnormal trend on {date}. Overall vibration levels increased from 2.1 mm/s to {vib} mm/s over {days} days. Spectrum analysis revealed dominant peaks at 1x and 2x running speed, indicating mechanical unbalance and possible misalignment. The motor was scheduled for emergency realignment. During the inspection, technicians found a cracked motor foot bolt, which had allowed gradual positional drift. {severity_text}",
    ],
    # Conveyor-related
    ("conveyor belt", "mechanical failure"): [
        "Conveyor belt system CB-{belt_id} in {location} experienced a belt splice failure on {date}. The vulcanized splice separated during loaded operation, causing the belt to stall and material to spill across the walkway. Workers in the area were evacuated as a precaution. The splice was {splice_age} months old, near the end of its expected service life. Belt tension was found to be {tension_pct}% above specification, likely accelerating splice degradation. {severity_text}",
        "On {date}, the return idler rollers on conveyor CB-{belt_id} at {location} seized, causing the belt to track off-center and contact the structural frame. Friction generated localized heating and minor surface damage to the belt edge. The seized rollers were replaced and belt tracking was adjusted. Root cause: failed roller bearings due to water ingress from a leaking roof above the conveyor gallery. {severity_text}",
    ],
    ("conveyor belt", "fire"): [
        "A fire was detected on conveyor CB-{belt_id} in {location} on {date} at {time}. The fire originated at a stuck idler roller where friction had ignited accumulated coal dust and rubber debris. The fire suppression system activated within {suppress_seconds} seconds. The fire was contained to a {damage_meters}-meter section of the belt. No injuries were reported, but production was halted for {downtime} hours. Investigation found that the dust cleanup schedule had not been followed for {missed_weeks} weeks. {severity_text}",
    ],
    ("conveyor belt", "fall"): [
        "On {date}, a maintenance technician slipped and fell from the elevated conveyor walkway at {location} while inspecting belt CB-{belt_id}. The worker fell approximately {fall_height} meters to the lower level. The walkway grating was found to be contaminated with spilled material and lubricant. The worker was wearing appropriate PPE including a hard hat, but was not clipped into the fall arrest system at the time of the incident. {severity_text}",
    ],
    # Forklift-related
    ("forklift", "crushing"): [
        "On {date} at approximately {time}, forklift FLT-{flt_id} struck a pedestrian worker in {location}. The forklift operator was reversing with an obstructed rear view due to a loaded pallet stacked above eye level. The pedestrian was walking in a designated forklift aisle without a high-visibility vest. The worker sustained a leg injury from being pinned against a storage rack. The area lacked operational proximity sensors or audible reverse alarms on the forklift. {severity_text}",
        "A loaded forklift FLT-{flt_id} tipped over on {date} in {location} while turning at excessive speed with the forks elevated. The operator was not wearing a seatbelt and was ejected from the cab. The load, consisting of {load_weight} kg of steel plate, shifted and fell. Adjacent workers were able to clear the area due to the slow tip-over. Contributing factors included wet floor surface and exceeding the rated load capacity by approximately {overload_pct}%. {severity_text}",
    ],
    ("forklift", "spill"): [
        "Forklift FLT-{flt_id} was transporting a drum of {chemical} through {location} on {date} when the drum fell from the forks due to improper securing. The drum ruptured on impact, spilling approximately {liters} liters of liquid across the warehouse floor. The spill reached the floor drain before containment measures could be deployed. Workers in the area were evacuated and the hazmat response team was called. Root cause: drum clamp attachment was damaged and had not been inspected per the daily checklist. {severity_text}",
    ],
    # Electrical panel
    ("electrical panel", "electrical shock"): [
        "An electrician received an electrical shock while performing maintenance on panel EP-{panel_id} at {location} on {date}. The panel was believed to be de-energized per the lockout/tagout procedure, but a secondary feed circuit remained live. The worker was wearing insulated gloves rated to {voltage}V, which prevented serious injury. Investigation revealed that the circuit diagram posted at the panel was outdated and did not reflect a modification made {months_ago} months ago that added the secondary feed. {severity_text}",
        "On {date}, an arc flash event occurred at electrical panel EP-{panel_id} in {location} during a switching operation. The arc flash produced temperatures estimated at {arc_temp}°C and expelled molten copper particles. The operator was wearing arc-rated PPE (40 cal/cm²) per the panel's arc flash label, which prevented burns. The root cause was identified as a deteriorated insulating barrier between bus bars, combined with the presence of conductive dust. {severity_text}",
    ],
    ("electrical panel", "fire"): [
        "A fire was reported in electrical panel EP-{panel_id} at {location} on {date} at {time}. The fire was caused by a loose connection on the main bus bar, which had been generating excessive heat over an extended period. Thermal discoloration and pitting were observed on adjacent conductors. The building's CO2 fire suppression system activated, extinguishing the fire within {suppress_seconds} seconds. Power to the affected section was interrupted for {downtime} hours during repair. {severity_text}",
    ],
    # Compressor
    ("compressor", "pressure buildup"): [
        "On {date}, compressor CMP-{cmp_id} at {location} experienced an overpressure event when the discharge pressure exceeded the safety relief valve (SRV) setpoint of {pressure_psi} PSI. The SRV opened correctly and vented the excess pressure to the atmosphere. Investigation found that the unloader valve had stuck in the loaded position due to a failed solenoid, causing the compressor to continue building pressure past the normal cutoff. {severity_text}",
        "Compressor CMP-{cmp_id} in {location} triggered a high-pressure alarm on {date}. The inter-stage pressure reached {pressure_psi} PSI, {psi_above} PSI above the rated operating pressure. The automatic shutdown was delayed by {delay_seconds} seconds due to a corroded pressure transducer providing intermittent readings. A manual emergency stop was initiated by the operator. Root cause: clogged air filter restricting inlet flow combined with the faulty pressure transducer. {severity_text}",
    ],
    ("compressor", "overheating"): [
        "Compressor CMP-{cmp_id} at {location} overheated on {date} after the oil cooling system malfunctioned. The discharge air temperature reached {temp}°C, triggering a high-temperature shutdown. The oil cooler was found to be severely fouled with particulate buildup, reducing cooling capacity by approximately {cooling_loss}%. Additionally, the oil level was found to be {oil_low} liters below the minimum mark, suggesting a slow leak at the shaft seal. {severity_text}",
    ],
    # Hydraulic press
    ("hydraulic press", "mechanical failure"): [
        "Hydraulic press HP-{press_id} in {location} experienced a cylinder seal failure on {date} during a pressing operation. Hydraulic fluid leaked at a rate of approximately {leak_rate} liters/minute, creating a slipping hazard on the shop floor. The press lost pressure and the ram drifted downward. The die protection system activated and held the load. Root cause: the cylinder seal was {seal_age} months past its recommended replacement interval. {severity_text}",
    ],
    ("hydraulic press", "crushing"): [
        "On {date}, an operator at hydraulic press HP-{press_id} in {location} had their hand caught in the die area when the light curtain safety system failed to detect the intrusion. The operator was reaching to reposition a workpiece that had shifted during the previous cycle. The two-hand control had been bypassed with a zip tie, defeating the safety interlock. The operator sustained crush injuries to two fingers. {severity_text}",
    ],
    # Welding station
    ("welding station", "fire"): [
        "A fire started at welding station WS-{ws_id} in {location} on {date} when welding sparks ignited flammable material stored improperly within {spark_distance} meters of the welding area. The fire watch personnel were not present at the time as they had been reassigned to another task. The fire was extinguished by nearby workers using a portable fire extinguisher. Damage was limited to {damage_description}. A hot work permit had been issued but the pre-work area inspection checklist had not been completed. {severity_text}",
    ],
    ("welding station", "chemical exposure"): [
        "On {date}, a welder at station WS-{ws_id} in {location} reported respiratory distress after welding on {material} without adequate local exhaust ventilation. The ventilation hood had been repositioned away from the welding plume to provide better workspace access. Air monitoring confirmed {contaminant} levels of {level} mg/m³, exceeding the PEL of {pel} mg/m³. The worker was sent for medical evaluation. The ventilation system was re-positioned and locked in place. {severity_text}",
    ],
}

# Templates for types that are not in the detailed mapping above (generic fallbacks)
GENERIC_TEMPLATES = [
    "An incident involving {equipment} was reported at {location} on {date}. The {hazard_type} event occurred during routine operations at approximately {time}. Workers in the immediate area reported {symptom} approximately {hours_before} hours before the event escalated. Emergency response was initiated per standard protocol. The area was secured and an investigation team was dispatched. Preliminary findings suggest {root_cause}. {severity_text}",
    "On {date}, a {report_type_text} was filed regarding {equipment} at {location}. During a scheduled inspection, maintenance personnel observed signs of {hazard_type}. The condition was documented and the equipment was tagged out for further evaluation. Historical maintenance records show {previous_issues} similar concerns flagged in the past {months_lookback} months. Corrective action has been initiated. {severity_text}",
    "Maintenance log entry for {equipment} at {location}, dated {date}. During preventive maintenance round, technician observed {observation} indicating potential {hazard_type} risk. Vibration readings were {vib_status} specification. Temperature measurements showed {temp_status}. The equipment was flagged for priority follow-up. Recommended actions include {recommended_action}. {severity_text}",
]

SEVERITY_DESCRIPTIONS = {
    "low": "The incident was classified as low severity. No injuries or significant equipment damage occurred. Corrective actions were implemented within the shift.",
    "medium": "The incident was classified as medium severity. Minor first-aid level treatment was required. Equipment was taken out of service for repairs lasting under 24 hours.",
    "high": "The incident was classified as high severity. Medical treatment beyond first aid was required and/or significant equipment damage occurred. The area was shut down pending investigation.",
    "critical": "The incident was classified as CRITICAL severity. Serious injury occurred and/or equipment was destroyed. A full root-cause investigation was mandated by management. Regulatory notification was initiated.",
}

SYMPTOMS = [
    "unusual noise",
    "visible smoke",
    "vibration increase",
    "temperature rise",
    "fluid leakage",
    "unusual smell",
    "sparking",
    "erratic operation",
]

ROOT_CAUSES = [
    "insufficient maintenance frequency",
    "operator error compounded by unclear procedures",
    "component fatigue beyond rated service life",
    "environmental conditions exceeding design parameters",
    "a recent modification that was not properly documented or reviewed",
    "degraded safety interlocks that were not tested per schedule",
    "supply chain substitution of a non-equivalent replacement part",
]

PREVIOUS_ISSUES = [
    "no", "1", "2", "3", "4 or more",
]

OBSERVATIONS = [
    "bearing wear patterns",
    "discoloration of insulation",
    "fluid seepage around seals",
    "corrosion on contact surfaces",
    "loose fastener hardware",
    "cracking in structural welds",
    "debris accumulation in cooling passages",
]

RECOMMENDED_ACTIONS = [
    "immediate component replacement and realignment",
    "increased monitoring frequency and scheduling a full overhaul at the next planned shutdown",
    "engineering review of the operating parameters and load profile",
    "retraining of operators on the updated standard operating procedure",
    "installation of additional monitoring sensors and updating the alarm setpoints",
]

CHEMICALS = ["hydraulic oil", "coolant concentrate", "degreaser solvent", "sulfuric acid solution", "lubricating grease"]
MATERIALS = ["galvanized steel", "stainless steel", "chromium alloy", "cadmium-plated bolts"]
CONTAMINANTS = ["hexavalent chromium", "manganese fumes", "zinc oxide fumes", "iron oxide particulates"]
DAMAGE_DESCRIPTIONS = ["a storage cabinet and several cardboard boxes", "paint on an adjacent wall and a rubber floor mat", "a stack of packaging materials and a fire extinguisher cabinet"]


def _random_date(start_year=2023, end_year=2025):
    """Generate a random date string."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_day = start + timedelta(days=random.randint(0, delta.days))
    return random_day.strftime("%Y-%m-%d")


def _random_time():
    """Generate a random time string."""
    hour = random.randint(0, 23)
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02d}:{minute:02d}"


def _generate_narrative(equipment, hazard_type, report_type, severity, location, date):
    """Generate a realistic narrative for a given equipment/hazard combination."""
    severity_text = SEVERITY_DESCRIPTIONS[severity]
    
    # Try to find a specific template for this equipment/hazard combo
    key = (equipment, hazard_type)
    if key in NARRATIVE_TEMPLATES:
        template = random.choice(NARRATIVE_TEMPLATES[key])
    else:
        template = random.choice(GENERIC_TEMPLATES)
    
    # Build a context dict with all possible template variables
    motor_ids = ["M-01", "M-02", "M-05", "M-07", "M-10", "M-12", "M-15", "M-18"]
    ctx = {
        "date": date,
        "time": _random_time(),
        "location": location,
        "severity_text": severity_text,
        "motor_id": random.choice(motor_ids),
        "temp": random.randint(85, 145),
        "hours_before": random.choice([1, 2, 3, 4, 6]),
        "run_hours": random.randint(1500, 8000),
        "line": random.randint(1, 4),
        "downtime": random.randint(2, 48),
        "seconds": random.randint(3, 15),
        "vib": round(random.uniform(4.0, 12.0), 1),
        "days": random.randint(3, 14),
        "belt_id": random.randint(101, 120),
        "splice_age": random.randint(18, 36),
        "tension_pct": random.randint(10, 25),
        "suppress_seconds": random.randint(5, 30),
        "damage_meters": random.randint(1, 5),
        "missed_weeks": random.randint(2, 8),
        "fall_height": round(random.uniform(1.5, 4.0), 1),
        "flt_id": random.randint(1, 20),
        "load_weight": random.randint(500, 3000),
        "overload_pct": random.randint(5, 25),
        "chemical": random.choice(CHEMICALS),
        "liters": random.randint(20, 200),
        "panel_id": random.randint(1, 30),
        "voltage": random.choice([600, 1000, 1500]),
        "months_ago": random.randint(3, 24),
        "arc_temp": random.randint(5000, 19000),
        "cmp_id": random.randint(1, 15),
        "pressure_psi": random.randint(125, 250),
        "psi_above": random.randint(10, 50),
        "delay_seconds": random.randint(3, 15),
        "cooling_loss": random.randint(30, 70),
        "oil_low": round(random.uniform(0.5, 3.0), 1),
        "press_id": random.randint(1, 10),
        "leak_rate": round(random.uniform(0.5, 5.0), 1),
        "seal_age": random.randint(6, 24),
        "ws_id": random.randint(1, 12),
        "spark_distance": round(random.uniform(1.0, 5.0), 1),
        "damage_description": random.choice(DAMAGE_DESCRIPTIONS),
        "material": random.choice(MATERIALS),
        "contaminant": random.choice(CONTAMINANTS),
        "level": round(random.uniform(0.05, 0.5), 3),
        "pel": round(random.uniform(0.01, 0.1), 3),
        "equipment": equipment,
        "hazard_type": hazard_type,
        "report_type_text": report_type.replace("_", " "),
        "symptom": random.choice(SYMPTOMS),
        "root_cause": random.choice(ROOT_CAUSES),
        "previous_issues": random.choice(PREVIOUS_ISSUES),
        "months_lookback": random.randint(3, 18),
        "observation": random.choice(OBSERVATIONS),
        "vib_status": random.choice(["within", "marginally above", "significantly above"]),
        "temp_status": random.choice(["normal readings", "slightly elevated readings", "readings trending upward"]),
        "recommended_action": random.choice(RECOMMENDED_ACTIONS),
    }
    
    # Format the template, ignoring missing keys
    try:
        return template.format(**ctx)
    except KeyError:
        # Fallback to a generic narrative
        return GENERIC_TEMPLATES[0].format(**ctx)


def _generate_title(equipment, hazard_type, report_type):
    """Generate a concise title for the report."""
    type_prefix = {
        "accident": "Accident",
        "near_miss": "Near-Miss",
        "maintenance_log": "Maintenance",
    }
    prefix = type_prefix.get(report_type, "Incident")
    
    title_templates = [
        f"{prefix}: {equipment.title()} {hazard_type} event",
        f"{prefix} Report — {hazard_type.title()} involving {equipment}",
        f"{equipment.title()} {hazard_type} — {prefix.lower()} report",
        f"{prefix}: {hazard_type.title()} hazard at {equipment} station",
    ]
    return random.choice(title_templates)


def generate_reports(num_reports=NUM_REPORTS, output_path=None):
    """Generate synthetic reports and write to JSON file."""
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "..", "data", "reports", "reports.json")
    
    reports = []
    
    # Ensure coverage: generate at least 2 reports per equipment type
    # and at least some for each report type
    equipment_queue = []
    for eq in EQUIPMENT_TYPES:
        equipment_queue.extend([eq] * 2)
    
    # Fill the rest randomly (weighted toward motors/conveyors for realism)
    equipment_weights = [0.25, 0.20, 0.15, 0.15, 0.10, 0.10, 0.05]
    remaining = num_reports - len(equipment_queue)
    for _ in range(remaining):
        equipment_queue.append(random.choices(EQUIPMENT_TYPES, weights=equipment_weights, k=1)[0])
    
    random.shuffle(equipment_queue)
    
    for i, equipment in enumerate(equipment_queue):
        report_id = f"RPT-{i+1:04d}"
        report_type = random.choices(REPORT_TYPES, weights=REPORT_TYPE_WEIGHTS, k=1)[0]
        severity = random.choices(SEVERITIES, weights=SEVERITY_WEIGHTS, k=1)[0]
        
        # Pick a hazard type that makes sense for the equipment
        # Get available hazards from the template mapping
        available_hazards = [h for (e, h) in NARRATIVE_TEMPLATES.keys() if e == equipment]
        if not available_hazards:
            available_hazards = HAZARD_TYPES[:5]
        hazard_type = random.choice(available_hazards)
        
        location = random.choice(LOCATIONS)
        date = _random_date()
        
        title = _generate_title(equipment, hazard_type, report_type)
        text = _generate_narrative(equipment, hazard_type, report_type, severity, location, date)
        
        report = {
            "id": report_id,
            "type": report_type,
            "title": title,
            "text": text,
            "equipment": equipment,
            "hazard_type": hazard_type,
            "location": location,
            "date": date,
            "severity": severity,
            "source": "synthetic",
        }
        reports.append(report)
    
    # Write to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(reports)} synthetic reports -> {output_path}")
    
    # Summary stats
    type_counts = {}
    eq_counts = {}
    for r in reports:
        type_counts[r["type"]] = type_counts.get(r["type"], 0) + 1
        eq_counts[r["equipment"]] = eq_counts.get(r["equipment"], 0) + 1
    print(f"  By type: {type_counts}")
    print(f"  By equipment: {eq_counts}")
    
    return reports


if __name__ == "__main__":
    generate_reports()
