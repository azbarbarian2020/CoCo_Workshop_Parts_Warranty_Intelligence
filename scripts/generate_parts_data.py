import os
import json
import random
import csv
from datetime import datetime, timedelta

random.seed(42)

PARTS = [
    ("TC-5000", "Turbocharger Assembly"),
    ("TCM-3200", "Transmission Control Module"),
    ("EXM-4100", "Exhaust Manifold Assembly"),
    ("ACM-2800", "Air Compressor Assembly"),
    ("SGB-6500", "Steering Gear Box"),
]

SUB_PARTS = {
    "TC-5000": [
        ("Turbine Wheel",              "SUP-003"),  # Allied Turbo Systems
        ("Compressor Wheel",           "SUP-003"),  # Allied Turbo Systems
        ("Bearing Housing",            "SUP-006"),  # Great Lakes Castings
        ("VGT Actuator",               "SUP-001"),  # default; multi-sourced below
        ("Wastegate Valve",            "SUP-005"),  # Pacific Valve & Fitting
        ("Oil Feed Line",              "SUP-012"),  # Heartland Steel Fabrication
        ("Heat Shield",                "SUP-009"),  # ThermalTech Coatings
    ],
    "TCM-3200": [
        ("Main PCB",                   "SUP-002"),  # default; multi-sourced below
        ("Solenoid Pack",              "SUP-001"),  # Precision Dynamics
        ("Wiring Harness",             "SUP-010"),  # Berg Elektronik
        ("Connector Housing",          "SUP-010"),  # Berg Elektronik
        ("Firmware Chip",              "SUP-002"),  # NovaTech Electronics
        ("Pressure Transducer",        "SUP-001"),  # Precision Dynamics
        ("Temperature Sensor",         "SUP-009"),  # ThermalTech Coatings
    ],
    "EXM-4100": [
        ("Manifold Casting",           "SUP-006"),  # Great Lakes Castings
        ("Gasket Set",                 "SUP-008"),  # Southeastern Gasket & Seal
        ("EGR Port Insert",            "SUP-006"),  # Great Lakes Castings
        ("Heat Shield",                "SUP-009"),  # ThermalTech Coatings
        ("Mounting Stud Kit",          "SUP-012"),  # Heartland Steel Fabrication
        ("Expansion Joint",            "SUP-005"),  # Pacific Valve & Fitting
        ("Pyrometer Boss",             "SUP-003"),  # Allied Turbo Systems
    ],
    "ACM-2800": [
        ("Compressor Head",            "SUP-006"),  # Great Lakes Castings
        ("Piston and Cylinder Kit",    "SUP-004"),  # default; multi-sourced below
        ("Unloader Valve",             "SUP-005"),  # Pacific Valve & Fitting
        ("Governor",                   "SUP-001"),  # Precision Dynamics
        ("Intake Filter",              "SUP-009"),  # ThermalTech Coatings
        ("Discharge Line Assembly",    "SUP-012"),  # Heartland Steel Fabrication
        ("Air Dryer Interface Gasket", "SUP-008"),  # Southeastern Gasket & Seal
    ],
    "SGB-6500": [
        ("Input Shaft Seal",           "SUP-008"),  # Southeastern Gasket & Seal
        ("Spool Valve",                "SUP-005"),  # Pacific Valve & Fitting
        ("Piston and Rack Assembly",   "SUP-006"),  # Great Lakes Castings
        ("Sector Shaft",               "SUP-012"),  # Heartland Steel Fabrication
        ("Housing Casting",            "SUP-006"),  # Great Lakes Castings
        ("Hydraulic Fitting Set",      "SUP-005"),  # Pacific Valve & Fitting
        ("Pitman Arm",                 "SUP-003"),  # Allied Turbo Systems
    ],
}

MULTI_SOURCE = {
    ("TC-5000", "VGT Actuator"): [
        ("SUP-001", 0.40),  # Precision Dynamics  — BAD BATCH story (one batch fails)
        ("SUP-003", 0.35),  # Allied Turbo Systems — clean
        ("SUP-009", 0.25),  # ThermalTech Coatings — clean
    ],
    ("TCM-3200", "Main PCB"): [
        ("SUP-002", 0.40),  # NovaTech Electronics — BAD SUPPLIER story (all batches fail)
        ("SUP-010", 0.35),  # Berg Elektronik — clean
        ("SUP-001", 0.25),  # Precision Dynamics — clean
    ],
    ("ACM-2800", "Piston and Cylinder Kit"): [
        ("SUP-004", 0.40),  # Midwest Pneumatics — DESIGN PROBLEM (all suppliers fail)
        ("SUP-006", 0.35),  # Great Lakes Castings — same rate
        ("SUP-012", 0.25),  # Heartland Steel — same rate
    ],
}

def pick_supplier(part_number, sub_part):
    key = (part_number, sub_part)
    if key in MULTI_SOURCE:
        suppliers, weights = zip(*MULTI_SOURCE[key])
        return random.choices(suppliers, weights=weights, k=1)[0]
    for sp, sid in SUB_PARTS[part_number]:
        if sp == sub_part:
            return sid
    raise ValueError(f"Unknown sub_part {sub_part} for {part_number}")

BAD_BATCHES = {
    ("TC-5000", "VGT Actuator", "SUP-001"):           "B-2024-PD-VA-07",
    ("TCM-3200", "Main PCB", "SUP-002"):              "B-2024-NT-MP-11",
    ("ACM-2800", "Piston and Cylinder Kit", "SUP-004"): "B-2023-MP-PCK-04",
}

BATCH_PREFIXES = {
    "SUP-001": "PD",
    "SUP-002": "NT",
    "SUP-003": "AT",
    "SUP-004": "MP",
    "SUP-005": "PV",
    "SUP-006": "GL",
    "SUP-008": "SG",
    "SUP-009": "TT",
    "SUP-010": "BE",
    "SUP-012": "HS",
}

SUB_PART_ABBREV = {}
_abbrev_counter = {}

def _register_abbrev(supplier_id, sub_part):
    initials = "".join(w[0] for w in sub_part.split()).upper()
    key = (supplier_id, initials)
    _abbrev_counter[key] = _abbrev_counter.get(key, 0) + 1
    suffix = "" if _abbrev_counter[key] == 1 else str(_abbrev_counter[key])
    SUB_PART_ABBREV[(supplier_id, sub_part)] = initials + suffix

for _pn, _subs in SUB_PARTS.items():
    for _sp, _sid in _subs:
        _register_abbrev(_sid, _sp)

for (_pn, _sp), _suppliers in MULTI_SOURCE.items():
    for _sid, _w in _suppliers:
        if (_sid, _sp) not in SUB_PART_ABBREV:
            _register_abbrev(_sid, _sp)

def generate_batches_for_sub_part(supplier_id, sub_part):
    prefix = BATCH_PREFIXES[supplier_id]
    sp_abbrev = SUB_PART_ABBREV[(supplier_id, sub_part)]
    batches = []
    for year in [2023, 2024]:
        for q in range(1, 5):
            batch_num = q + (0 if year == 2023 else 4)
            batches.append(f"B-{year}-{prefix}-{sp_abbrev}-{batch_num:02d}")
    return batches

SUB_PART_BATCHES = {}
for _pn, _subs in SUB_PARTS.items():
    for _sp, _sid in _subs:
        key = (_sid, _sp)
        if key not in SUB_PART_BATCHES:
            SUB_PART_BATCHES[key] = generate_batches_for_sub_part(_sid, _sp)

for (_pn, _sp), _suppliers in MULTI_SOURCE.items():
    for _sid, _w in _suppliers:
        key = (_sid, _sp)
        if key not in SUB_PART_BATCHES:
            SUB_PART_BATCHES[key] = generate_batches_for_sub_part(_sid, _sp)

BAD_BATCH_RATE = 0.35
START_DATE = datetime(2023, 6, 1)
END_DATE = datetime(2025, 3, 31)
DAYS_RANGE = (END_DATE - START_DATE).days

rows = []
serial_counters = {pn: 0 for pn, _ in PARTS}

for part_number, part_description in PARTS:
    count = 5000
    for i in range(count):
        serial_counters[part_number] += 1
        sn_prefix = part_number.replace("-", "")
        serial_number = f"PSN-{sn_prefix}-{serial_counters[part_number]:05d}"

        manufacture_date = START_DATE + timedelta(days=random.randint(0, DAYS_RANGE))

        bom = []
        for sub_part, default_supplier_id in SUB_PARTS[part_number]:
            supplier_id = pick_supplier(part_number, sub_part)

            bad_key = (part_number, sub_part, supplier_id)
            if bad_key in BAD_BATCHES and random.random() < BAD_BATCH_RATE:
                batch_id = BAD_BATCHES[bad_key]
            else:
                batch_id = random.choice(SUB_PART_BATCHES[(supplier_id, sub_part)])

            bom.append({
                "sub_part": sub_part,
                "supplier_id": supplier_id,
                "batch_id": batch_id,
            })

        rows.append({
            "serial_number": serial_number,
            "part_number": part_number,
            "part_description": part_description,
            "manufacture_date": manufacture_date.strftime("%Y-%m-%d"),
            "bom": json.dumps(bom),
        })

output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "parts.csv")
with open(output_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["serial_number", "part_number", "part_description", "manufacture_date", "bom"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} parts to {output_path}")

bad_batch_ids = set(BAD_BATCHES.values())
bad_batch_counts = {}
for r in rows:
    bom = json.loads(r["bom"])
    for item in bom:
        if item["batch_id"] in bad_batch_ids:
            key = (r["part_number"], item["sub_part"], item["batch_id"])
            bad_batch_counts[key] = bad_batch_counts.get(key, 0) + 1

print("\nBad batch distribution:")
for (pn, sp, batch), cnt in sorted(bad_batch_counts.items()):
    print(f"  {pn} / {sp} / {batch}: {cnt} parts")

print("\nMulti-source supplier distribution:")
for (pn, sp), suppliers in MULTI_SOURCE.items():
    print(f"  {pn} / {sp}:")
    supplier_counts = {}
    for r in rows:
        if r["part_number"] != pn:
            continue
        bom = json.loads(r["bom"])
        for item in bom:
            if item["sub_part"] == sp:
                sid = item["supplier_id"]
                supplier_counts[sid] = supplier_counts.get(sid, 0) + 1
    for sid, cnt in sorted(supplier_counts.items()):
        pct = cnt / 5000 * 100
        print(f"    {sid}: {cnt} ({pct:.1f}%)")
