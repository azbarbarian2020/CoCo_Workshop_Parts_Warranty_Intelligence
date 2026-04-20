import os
import json
import random
import csv
from datetime import datetime, timedelta

random.seed(99)

_BASE = os.path.dirname(os.path.dirname(__file__))
PARTS_CSV = os.path.join(_BASE, "data", "parts.csv")
OUTPUT_CSV = os.path.join(_BASE, "data", "warranty_claims.csv")

parts = []
with open(PARTS_CSV) as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["bom_parsed"] = json.loads(row["bom"])
        parts.append(row)

parts_by_pn = {}
for p in parts:
    parts_by_pn.setdefault(p["part_number"], []).append(p)

BAD_BATCH_IDS = {
    "TC-5000":  ("VGT Actuator",           "SUP-001", "B-2024-PD-VA-07"),
    "TCM-3200": ("Main PCB",               "SUP-002", None),
}

DESIGN_PROBLEM_PARTS = {"ACM-2800": "Piston and Cylinder Kit"}

def has_bad_batch(part):
    pn = part["part_number"]
    if pn not in BAD_BATCH_IDS:
        return False
    sub_part, bad_supplier, bad_batch = BAD_BATCH_IDS[pn]
    for item in part["bom_parsed"]:
        if item["sub_part"] != sub_part:
            continue
        if bad_batch is not None:
            if item["batch_id"] == bad_batch:
                return True
        elif bad_supplier is not None:
            if item["supplier_id"] == bad_supplier:
                return True
    return False

def get_bad_sub_part(part):
    pn = part["part_number"]
    return BAD_BATCH_IDS[pn][0]

DEALERS = [f"DLR-{i:04d}" for i in range(1, 26)]

CUSTOMER_COMPLAINTS = {
    "TC-5000": {
        "VGT Actuator": [
            "Truck has no power going uphill with a full load",
            "Losing boost pressure intermittently on highway",
            "Check engine light on, feels like turbo isn't kicking in",
            "Power drops off randomly during acceleration",
            "Black smoke and low power, especially under load",
            "Turbo seems sluggish, takes forever to build boost",
            "Lost power on mountain grade, barely made it to the top",
            "Engine feels choked, no turbo response when I floor it",
            "Boost gauge reads low, truck struggles with trailer",
            "Intermittent power loss, sometimes fine sometimes not",
            "CEL on, codes pointing to turbo, power is way down",
            "No boost at all now, was intermittent last week",
            "Truck won't pull grades anymore, used to be fine",
            "Turbo lag is getting worse every day",
            "Driver says it feels like driving without a turbo",
            "Power loss under load, been getting worse for 2 weeks",
            "Can't maintain speed on hills, turbo feels dead",
            "Boost comes and goes, mostly goes lately",
            "Engine derate on grades, turbo whistle sounds wrong",
            "Complete loss of boost pressure, truck barely moves loaded",
        ],
        "Turbine Wheel": [
            "Terrible screeching noise from turbo area",
            "Metal grinding sound that gets louder with RPM",
            "High pitched whine from engine compartment",
            "Turbo sounds like it's coming apart",
            "Grinding noise and loss of power at same time",
        ],
        "Compressor Wheel": [
            "Oil in the intake piping, turbo seems to be leaking",
            "Charge air cooler full of oil, turbo related",
            "Blue smoke at startup and oil everywhere in the intake",
        ],
        "Bearing Housing": [
            "Turbo whine getting louder, shaft play when I checked",
            "Excessive oil consumption and turbo noise",
            "Turbo sounds rough, oil dripping from turbo drain",
            "Whining noise from turbo, oil on the exhaust side",
        ],
        "Wastegate Valve": [
            "Over-boosting on cold starts, boost gauge pegged",
            "Turbo surging at steady throttle, can hear it cycling",
            "Boost spikes way too high then drops off",
        ],
        "Oil Feed Line": [
            "Turbo smoking badly, low oil pressure warning",
            "Smell burning oil near turbo, low oil level",
        ],
        "Heat Shield": [
            "Wiring near turbo melted, electrical issues started",
            "Burning smell from engine, found melted wire loom near turbo",
        ],
    },
    "TCM-3200": {
        "Main PCB": [
            "Transmission shifting all over the place randomly",
            "Truck goes into limp mode for no reason then comes back",
            "Harsh shifting and check trans light keeps flickering",
            "Intermittent limp mode, sometimes clears on restart",
            "Shifts are rough one day smooth the next, no pattern",
            "Trans acts up in cold weather but fine when warm",
            "Random gear hunting on the highway, cruise control on",
            "Shifting erratically, dealer reset codes but came back",
            "Limp mode twice this week, no consistent trigger",
            "Transmission feels confused, shifts too early then too late",
            "Check trans light intermittent, shifts hard when it comes on",
            "Trans slams into gear sometimes, other times perfect",
            "Unpredictable shifting, driver afraid to take the highway",
            "Codes keep coming back after clearing, shifting rough",
            "Limp mode on cold mornings, clears after 20 minutes",
            "Trans shifts fine then suddenly bangs into third gear",
        ],
        "Solenoid Pack": [
            "Delayed engagement when shifting from park to drive",
            "Noticeable delay shifting between gears especially 2 to 3",
            "Truck rolls before transmission catches when starting out",
            "Engagement feels soft, like it slips before grabbing",
            "Slow to respond when you give it throttle from a stop",
        ],
        "Wiring Harness": [
            "Trans goes to limp mode when driving over bumps",
            "Intermittent communication error with trans module",
            "Trans fault codes appear and disappear randomly",
            "Transmission loses communication going over railroad tracks",
        ],
        "Connector Housing": [
            "Trans module throwing connector fault codes after rain",
            "Water got in the trans connector, now intermittent faults",
            "Corrosion on trans plug, shifting issues in wet weather",
        ],
        "Firmware Chip": [
            "Trans never seems to learn driver habits, always hunting",
            "Shift points make no sense for the load we're carrying",
        ],
        "Pressure Transducer": [
            "Shift quality varies wildly between gears",
            "Harsh 3-4 shift but all others are smooth",
            "Shifting pressure seems off, some gears bang some slip",
        ],
        "Temperature Sensor": [
            "Trans acts up only when it's really hot outside",
            "Shifting problems start after an hour of driving",
            "Trans fine in morning, terrible in afternoon heat",
        ],
    },
    "EXM-4100": {
        "Heat Shield": [
            "Burning smell from engine, wiring looks melted near exhaust",
            "Something smells hot under the hood after a long run",
            "Found melted wire loom and discolored paint near manifold",
            "Electrical gremlins started, think something melted near exhaust",
            "Burning plastic smell after pulling grades",
        ],
        "Gasket Set": [
            "Ticking noise from exhaust that gets louder with RPM",
            "Exhaust leak sound at the manifold, louder when cold",
            "Can smell exhaust in the cab at idle",
            "Ticking on cold start that goes away when warm",
        ],
        "Manifold Casting": [
            "Visible crack in the exhaust manifold",
            "Exhaust leak from the manifold itself not the gaskets",
            "Manifold is cracked, you can see daylight through it",
        ],
        "EGR Port Insert": [
            "Engine running rough, EGR codes showing up",
            "Loss of power and EGR fault codes",
            "EGR system not flowing right, poor performance",
        ],
        "Mounting Stud Kit": [
            "Exhaust manifold is loose, studs look stretched",
            "Manifold rattling, one stud broke off",
        ],
        "Expansion Joint": [
            "Exhaust leak right where manifold meets the turbo",
            "Hissing from the turbo connection on the manifold",
        ],
        "Pyrometer Boss": [
            "EGT readings jumping all over the place",
            "Temp gauge for exhaust is reading crazy numbers",
        ],
    },
    "ACM-2800": {
        "Piston and Cylinder Kit": [
            "Air tanks take forever to build up pressure",
            "Air system pressure builds really slow now",
            "Low air warning keeps coming on during city driving",
            "Compressor runs constantly but pressure barely climbs",
            "Takes 10 minutes to build air, used to take 3",
            "Air pressure won't hold, compressor cycling nonstop",
            "Slow air build up, can hear air leaking at compressor",
            "Low air buzzer going off all the time",
            "Air pressure drops when sitting at idle",
            "Compressor struggles to maintain system pressure",
            "Air tanks won't fill to cutoff anymore",
            "Slow pressure build and oil in the air tanks",
        ],
        "Governor": [
            "Compressor cuts in and out way too often",
            "Air compressor cycling rapidly, never settles",
            "Compressor won't shut off, runs continuously",
        ],
        "Compressor Head": [
            "Hissing from the compressor head area",
            "Air leaking from the compressor, can hear it",
            "Air leak at the compressor, pressure drops at idle",
        ],
        "Unloader Valve": [
            "Compressor won't unload, runs hot all the time",
            "Compressor head is extremely hot, unloader not working",
        ],
        "Intake Filter": [
            "Oil all over the compressor intake filter area",
            "Compressor intake filter soaked with oil",
        ],
        "Discharge Line Assembly": [
            "Air leak in the line between compressor and first tank",
            "Can hear air escaping from a discharge line fitting",
        ],
        "Air Dryer Interface Gasket": [
            "Air leak where compressor meets the air dryer",
            "Oil contamination in the air dryer, leaking at gasket",
        ],
    },
    "SGB-6500": {
        "Sector Shaft": [
            "Steering has a lot of play, wanders on the highway",
            "Steering feels vague, truck drifts in the lane",
            "Front end wanders at highway speed, constant correction needed",
            "Steering wheel has excessive free play",
        ],
        "Piston and Rack Assembly": [
            "Steering wanders badly at highway speed",
            "Truck pulls to one side, steering feels loose",
            "Can't keep the truck in the lane without fighting it",
        ],
        "Input Shaft Seal": [
            "Power steering fluid leaking at the steering column",
            "Fluid dripping from where the shaft goes into the gearbox",
            "Steering fluid leak at the input shaft, low fluid",
        ],
        "Housing Casting": [
            "Steering effort is way higher than normal",
            "Power steering feels like it's not working sometimes",
            "Takes a lot more effort to turn the wheel lately",
        ],
        "Spool Valve": [
            "Groaning noise when turning the steering wheel",
            "Moaning sound from steering gearbox on turns",
        ],
        "Hydraulic Fitting Set": [
            "Steering fluid leak at one of the line connections",
            "Power steering line fitting is weeping fluid",
        ],
        "Pitman Arm": [
            "Clunking from steering when changing direction",
            "Knock in the steering when going from left to right",
        ],
    },
}

TECH_NOTES_TEMPLATES = {
    "TC-5000": {
        "VGT Actuator": [
            "Replaced TC-5000 Turbocharger Assembly. Found VGT Actuator stuck in partially open position. Vane ring not responding to electronic commands. Actuator rod showed signs of carbon buildup preventing full travel. No other sub-components showed damage.",
            "Replaced TC-5000 assembly. VGT Actuator failure confirmed. Actuator not responding to ECM signal. Disassembled and found internal gear mechanism seized. Rest of turbo in acceptable condition.",
            "Turbo replacement performed. VGT Actuator was binding intermittently. Could reproduce failure when actuator was cold. Electrical connector and wiring checked good. Issue is mechanical inside the actuator unit.",
            "Removed and replaced TC-5000. Root cause is VGT Actuator - not reaching commanded position. Diagnostic showed actuator position deviation fault. Turbo shaft play within spec. Bearing housing oil seal dry but intact.",
            "TC-5000 replaced due to VGT Actuator failure. Actuator motor drawing excessive current. Position feedback erratic. Inspected turbine and compressor wheels - no contact damage. Oil feed line clear.",
            "Replaced turbocharger assembly. VGT Actuator completely non-functional. Could not command any vane movement with scan tool. Electrical checks at connector passed. Internal actuator fault. Wastegate Valve operated normally when tested.",
            "TC-5000 swap. VGT Actuator failed closed causing persistent over-boost condition. Wastegate compensating but customer noticed power fluctuations. Actuator linkage corroded and frozen. Heat Shield showed slight discoloration but still serviceable.",
            "Replaced TC-5000 unit. Confirmed VGT Actuator fault with diagnostic scan. Actuator sluggish when cold and non-responsive at operating temp. Bearing Housing had minor oil residue but within tolerance. Primary failure is actuator.",
            "Turbo assembly replaced. VGT Actuator intermittent - works sometimes and sticks other times. Carbon deposit on vane ring pivot points traced back to actuator not cycling properly. Compressor side clean.",
            "TC-5000 replacement. VGT Actuator position sensor out of range. Mechanical inspection showed actuator arm bent slightly. Likely fatigue failure. Rest of turbo components appear in good shape.",
            "Removed failed TC-5000. VGT Actuator shaft seal leaking exhaust gas into actuator housing. Internal corrosion and carbon fouling. Motor still functional but position accuracy gone. Turbine Wheel had minor tip erosion but was not the primary issue.",
            "TC-5000 replaced. VGT Actuator calibration way off, could not recalibrate with scan tool. Suspect internal potentiometer failure. All other turbo components inspected and within spec.",
            "Full turbo replacement. VGT Actuator response time exceeding 2 seconds, should be under 200ms. Slow response causing boost control issues. Cleaned and tested - still slow. Bearing Housing oil supply adequate.",
            "Replaced TC-5000 turbo. VGT Actuator found mechanically locked in mid-position. Applied manual force to free it but returned to stuck position under exhaust load. Oil Feed Line checked clear. Heat Shield secure.",
            "TC-5000 assembly removed. VGT Actuator electrical failure - open circuit in actuator motor winding. Connector pins clean and tight. Wiring harness continuity good to ECM. Internal actuator motor failure.",
        ],
        "VGT Actuator_cascade": [
            "Replaced TC-5000. VGT Actuator failure was primary cause. Actuator stuck closed causing sustained over-boost that appears to have stressed the Wastegate Valve spring beyond limits. Both sub-components damaged. Recommend reviewing boost control logic.",
            "TC-5000 replaced. VGT Actuator seized causing uncontrolled boost. Extended over-boost condition led to Turbine Wheel tip contact with housing. Found aluminum transfer marks on turbine housing bore. VGT failure initiated the cascade.",
            "Replaced turbo assembly. VGT Actuator failed causing erratic boost. Prolonged operation in this condition caused excessive heat cycling on the Heat Shield which is now warped and cracking. VGT Actuator is root cause, Heat Shield is collateral damage.",
        ],
        "Turbine Wheel": [
            "Replaced TC-5000. Turbine Wheel has visible blade damage - two blades cracked at root. Metal debris found in turbine housing. Bearing Housing contaminated with metal particles. Turbine Wheel fatigue failure is root cause.",
            "TC-5000 assembly replaced. Turbine Wheel failure - blade liberation event. One blade missing entirely. Scoring on housing bore. Oil Feed Line intact. Compressor side undamaged. FOD from turbine side only.",
        ],
        "Compressor Wheel": [
            "Replaced TC-5000. Compressor Wheel seal failure allowing oil migration into charge air system. Charge air cooler contaminated. Bearing Housing oil seal on compressor side deteriorated. Compressor Wheel inducer shows light rub marks.",
        ],
        "Bearing Housing": [
            "TC-5000 replaced. Bearing Housing failure - excessive shaft radial play measured at 0.015 inches, spec is 0.003 max. Oil drain showed metal contamination. Both wheels have rub marks from shaft deflection. Bearing is root cause.",
            "Replaced turbo. Bearing Housing oil seal failure on exhaust side causing external oil leak and smoke. Shaft play at limit. Oil Feed Line flow tested normal. Bearing wear is the failure.",
        ],
        "Wastegate Valve": [
            "Replaced TC-5000. Wastegate Valve stuck fully open. Spring broken. Unable to control boost pressure. Turbo cannot build boost above 5 PSI. All other components inspected and serviceable.",
        ],
        "Oil Feed Line": [
            "TC-5000 replaced. Oil Feed Line partially blocked with carbon deposits. Oil starvation caused bearing damage. Shaft play now excessive. Oil line restriction is the initiating failure.",
        ],
        "Heat Shield": [
            "Replaced TC-5000 due to heat damage. Heat Shield cracked and separated allowing exhaust temps to damage adjacent wiring and the VGT Actuator connector. Heat Shield is primary failure, VGT connector melted as secondary damage.",
        ],
    },
    "TCM-3200": {
        "Main PCB": [
            "Replaced TCM-3200 Transmission Control Module. Main PCB showing intermittent solder joint failures on the main processor. Cold solder joints visible under magnification. Reflowed connections temporarily but failure returned. PCB replacement needed.",
            "TCM-3200 replaced. Main PCB fault confirmed with dealer diagnostic tool. Internal communication errors between processor and solenoid drivers on the PCB. No external damage. Connector pins clean. Board-level failure.",
            "Removed and replaced TCM-3200. Main PCB capacitor failure causing voltage regulation issues. Module resets intermittently under vibration. Wiring Harness and Connector Housing both tested good. Purely internal PCB defect.",
            "TCM-3200 swap. Main PCB diagnosed as root cause of intermittent shift faults. Power supply section of the board shows thermal discoloration. Board is failing under heat soak conditions. Firmware version current.",
            "Replaced transmission control module. Main PCB has micro-crack in power trace visible under scope. Fault intermittent - vibration and temperature dependent. Solenoid Pack resistance values all normal. PCB defect only.",
            "TCM-3200 replaced. Main PCB EEPROM corruption detected during diagnostic download. Module storing invalid adaptive values. Could not reprogram - EEPROM failure. All connected sensors and solenoids test normal.",
            "Replaced TCM-3200. Main PCB driver circuit for shift solenoids failing intermittently. Module commands gear change but signal never reaches solenoid. Internal board trace issue. Solenoid Pack tested independently and works fine.",
            "TCM-3200 replacement. Found Main PCB ground plane deterioration causing erratic sensor readings. Module seeing phantom signals. Pressure Transducer and Temperature Sensor both verified accurate with external gauge. PCB is the problem.",
            "Removed failed TCM-3200. Main PCB relay on the board clicking but not making consistent contact. Causes momentary power loss to solenoid drivers. Random harsh shift complaints match relay dropout pattern.",
            "TCM-3200 replaced. Main PCB analog to digital converter failing. Module reading incorrect voltage from all pressure sensors even though sensor output is correct. Board-level ADC chip failure.",
            "Replaced module. Main PCB has water intrusion damage despite sealed housing. Suspect condensation from temperature cycling. Corrosion on several IC pins. Connector Housing seal was intact so moisture came from within.",
        ],
        "Main PCB_cascade": [
            "TCM-3200 replaced. Main PCB failure caused sustained incorrect line pressure commands which damaged Solenoid Pack. Two solenoids showing burnt coils from excessive duty cycle commanded by failed board. PCB is root cause.",
            "Replaced TCM-3200. Main PCB fault causing erratic pressure commands. Extended operation burned out the Pressure Transducer from constant overcurrent sensing requests. Main PCB failure is primary.",
        ],
        "Solenoid Pack": [
            "Replaced TCM-3200. Solenoid Pack failure - shift solenoid B stuck closed. Resistance out of spec at 2.1 ohms vs 5.5 spec. Clean break in coil winding. Main PCB tested normal with substitute solenoid. Solenoid is the failure.",
            "TCM-3200 replaced. Solenoid Pack engagement delay caused by weak spring return on the main clutch solenoid. Response time measured at 340ms vs 80ms spec. Electrical values normal but mechanical response degraded.",
        ],
        "Wiring Harness": [
            "Replaced TCM-3200. Found Wiring Harness chafed against frame bracket. Intermittent short on CAN bus line causing communication dropouts. Repaired harness routing but replaced module as precaution due to possible ECM damage from shorts.",
            "TCM-3200 replaced. Wiring Harness internal break in shielding causing electromagnetic interference. Fault only appears near certain radio towers. Replaced harness section and module.",
        ],
        "Connector Housing": [
            "Replaced TCM-3200. Connector Housing seal failed allowing moisture intrusion. Found green corrosion on pins 4, 7, and 12. Water caused intermittent connection. Module internals showed no water damage. Connector failed.",
        ],
        "Firmware Chip": [
            "TCM-3200 replaced. Firmware Chip not accepting adaptive learning updates. Transmission never optimizes shift points. Module stuck on default calibration. Reprogramming attempts failed. Chip defect suspected.",
        ],
        "Pressure Transducer": [
            "Replaced TCM-3200. Pressure Transducer output drifting under temperature. Line pressure reading 40 PSI high at operating temp. External gauge confirms actual pressure is correct. Transducer element failing.",
        ],
        "Temperature Sensor": [
            "TCM-3200 replaced. Temperature Sensor reading 30 degrees low at operating temp. Module commanding wrong shift strategy. Verified with external thermometer. Sensor failure causing inappropriate shift scheduling.",
        ],
    },
    "EXM-4100": {
        "Heat Shield": [
            "Replaced EXM-4100 Exhaust Manifold Assembly. Heat Shield cracked and partially detached. Adjacent wiring harness showing heat damage. Underhood temps at manifold measured 200F above normal. Heat Shield failure allowed direct exhaust radiation to nearby components.",
            "EXM-4100 replaced. Heat Shield deteriorated from thermal cycling. Found warped and cracking at mounting points. Expansion Joint showing accelerated aging from excess heat exposure. Heat Shield is primary failure.",
            "Replaced exhaust manifold assembly. Heat Shield material delaminating. Insulation layer gone in two spots. Wiring loom directly above shows melted outer jacket. Heat Shield failure is root cause of thermal damage.",
            "EXM-4100 swap. Heat Shield has multiple fractures. Thermal imaging showed surface temps 400F higher than sister truck. Found early stage heat discoloration on Expansion Joint bellows directly behind missing Heat Shield section.",
            "Replaced manifold. Heat Shield mounting tabs fatigued and broken. Shield sagging onto manifold surface. Adjacent electrical connector partially melted. Heat Shield must be replaced, electrical damage is secondary.",
        ],
        "Heat Shield_cascade": [
            "EXM-4100 replaced. Heat Shield failed first, causing Expansion Joint bellows to overheat and crack. Found exhaust leak at turbo interface as a result. Two-part failure chain starting with Heat Shield.",
            "Replaced EXM-4100. Heat Shield failure exposed adjacent components to direct exhaust heat. Expansion Joint bellows hardened and cracked. Also found early stage heat damage on Pyrometer Boss wiring. Heat Shield root cause.",
        ],
        "Gasket Set": [
            "Replaced EXM-4100. Gasket Set failure at cylinder 3 port. Visible blow-by pattern on gasket surface. Manifold face checked flat. Stud torques were in spec. Gasket material failed.",
            "EXM-4100 replaced. Gasket Set leaking at two cylinder ports. Exhaust soot pattern visible on gasket faces. Ticking noise confirmed as exhaust leak. Manifold Casting surface inspected - no cracks.",
        ],
        "Manifold Casting": [
            "Replaced EXM-4100. Manifold Casting has thermal fatigue crack between cylinders 2 and 3. Crack propagated through wall. Visible exhaust leak. Casting failure from thermal stress cycling.",
            "EXM-4100 replaced. Found hairline crack in Manifold Casting at EGR port junction. Crack not visible externally but confirmed with dye penetrant. Casting defect at stress riser.",
        ],
        "EGR Port Insert": [
            "Replaced EXM-4100. EGR Port Insert heavily carboned causing flow restriction. EGR flow test failed. Insert bore reduced by approximately 40 percent. Engine running rich due to EGR underflow.",
        ],
        "Mounting Stud Kit": [
            "EXM-4100 replaced. Two Mounting Stud Kit studs stretched beyond spec. One stud broken flush with block. Manifold was loose causing exhaust leak. Stud failure from thermal cycling.",
        ],
        "Expansion Joint": [
            "Replaced EXM-4100. Expansion Joint bellows cracked circumferentially. Exhaust leak at turbo interface. Joint lost flexibility from age and thermal cycles. No other manifold damage.",
        ],
        "Pyrometer Boss": [
            "EXM-4100 replaced. Pyrometer Boss thread seal failed. Getting false EGT readings. Pyrometer seating surface eroded from exhaust gas blow-by. Sensor readings unreliable.",
        ],
    },
    "ACM-2800": {
        "Piston and Cylinder Kit": [
            "Replaced ACM-2800 Air Compressor Assembly. Piston and Cylinder Kit worn beyond service limits. Cylinder bore out of round by 0.004 inches. Piston ring end gap excessive at 0.035 inches vs 0.015 max. Compressor cannot maintain adequate volume output.",
            "ACM-2800 replaced. Piston and Cylinder Kit failure. Piston ring broken into three pieces. Scoring on cylinder wall. Metal debris in discharge. Build time to governor cut-out exceeds 8 minutes, spec is 3.",
            "Replaced air compressor. Piston and Cylinder Kit bore wear causing blow-by. Air output measured at 40 percent of rated CFM. Oil passing rings into air system. Kit is worn out.",
            "ACM-2800 swap. Piston and Cylinder Kit failure confirmed with leak-down test. 60 percent leakage past rings at TDC. Normal is under 15 percent. Cylinder has vertical scoring. Compressor head gasket still sealing.",
            "Replaced ACM-2800. Piston and Cylinder Kit is root cause. Piston wrist pin shows wear allowing piston rock. Cylinder bore tapered 0.003 inches. Governor and Unloader Valve functioning normally.",
            "ACM-2800 replaced. Piston and Cylinder Kit worn. Excessive oil carryover into air system. Oil found in air tanks and air dryer was saturated. Cylinder Kit causing both pressure loss and oil contamination.",
            "Replaced compressor assembly. Piston and Cylinder Kit failure. Compression test showed only 60 PSI, should be above 120. Discharge valve good. Intake valve good. Cylinder Kit is the bottleneck.",
            "ACM-2800 replaced due to Piston and Cylinder Kit wear. Build time to 120 PSI over 7 minutes. Spec is under 3 minutes. Bore measurement confirms taper and out of round. Governor cutting in and out normally.",
            "Replaced air compressor. Piston and Cylinder Kit causing slow build. Driver reports low air warnings during stop and go driving. Compressor output insufficient for brake system demand. Kit is shot.",
            "ACM-2800 replacement. Piston and Cylinder Kit worn - rings stuck in grooves from oil carbon. Blow-by excessive. Air Dryer Interface Gasket also oil soaked but not leaking. Piston Kit is primary.",
        ],
        "Piston and Cylinder Kit_cascade": [
            "ACM-2800 replaced. Piston and Cylinder Kit failure causing oil to pass into air system. Oil contamination destroyed the Air Dryer Interface Gasket downstream. Both failed but Piston Kit is root cause.",
            "Replaced ACM-2800. Worn Piston and Cylinder Kit caused sustained oil carryover which fouled the Intake Filter and contaminated the Governor diaphragm. Multiple secondary failures all traced back to Piston Kit wear.",
        ],
        "Governor": [
            "Replaced ACM-2800. Governor not maintaining proper cut-in and cut-out pressure. Cycling between 95 and 105 PSI instead of 100 and 130. Diaphragm has small tear. Governor failure only.",
            "ACM-2800 replaced. Governor stuck in unloaded position. Compressor running but not building pressure above 80 PSI. Governor bypass test restored normal pressure. Governor defective.",
        ],
        "Compressor Head": [
            "Replaced ACM-2800. Compressor Head cracked at discharge port. Audible air leak when compressor loaded. Head gasket intact but head casting has fatigue crack. Compressor Head failure.",
            "ACM-2800 replaced. Compressor Head valve plate eroded. Discharge valve not sealing. Compressor pumping air back and forth instead of building pressure. Head assembly failure.",
        ],
        "Unloader Valve": [
            "Replaced ACM-2800. Unloader Valve stuck in loaded position. Compressor running hot, head temperature over 350F. Unloader piston corroded in bore. Valve failure causing overheating.",
        ],
        "Intake Filter": [
            "ACM-2800 replaced. Intake Filter completely oil saturated and restricted. Compressor starving for air. Output reduced but cylinder and rings check OK. Filter failure from oil contamination source unknown.",
        ],
        "Discharge Line Assembly": [
            "Replaced ACM-2800. Discharge Line Assembly has cracked fitting at compressor outlet. Air leak under pressure. Line vibration fatigue at the connection point. Tightening didn't help, fitting is cracked.",
        ],
        "Air Dryer Interface Gasket": [
            "ACM-2800 replaced. Air Dryer Interface Gasket blown out. Air leak between compressor discharge and air dryer inlet. Gasket material deteriorated. Connection retorqued but gasket won't seal.",
        ],
    },
    "SGB-6500": {
        "Sector Shaft": [
            "Replaced SGB-6500 Steering Gear Box. Sector Shaft has excessive spline wear. Measured 0.008 inch play at output vs 0.002 spec. Steering wanders at highway speed requiring constant correction. Sector Shaft wear is root cause.",
            "SGB-6500 replaced. Sector Shaft bearing surface worn creating play in the gear mesh. Steering has dead zone in center. Adjustment cannot compensate for shaft wear. Need full unit replacement.",
            "Replaced steering gearbox. Sector Shaft wear causing excessive free play. Driver cannot hold lane on highway. Adjusted to minimum lash but still exceeds spec. Shaft surfaces are worn.",
        ],
        "Sector Shaft_cascade": [
            "SGB-6500 replaced. Sector Shaft wear caused excessive movement that wore out the Pitman Arm spline connection. Both components show damage. Sector Shaft wear initiated the looseness.",
        ],
        "Piston and Rack Assembly": [
            "Replaced SGB-6500. Piston and Rack Assembly seal leaking internally. Power assist working but steering wanders as fluid bypasses the piston. External leak test passed. Internal bypass confirmed on bench.",
            "SGB-6500 replaced. Piston and Rack Assembly teeth worn on one side causing uneven steering effort left vs right. Probable impact damage at some point. Rack surface pitted.",
        ],
        "Input Shaft Seal": [
            "Replaced SGB-6500. Input Shaft Seal leaking power steering fluid at the column connection. Fluid on the floor under the dash. Seal has hardened and cracked from age. No shaft damage.",
            "SGB-6500 replaced. Input Shaft Seal failure causing external fluid leak. Low fluid triggered hard steering complaint. Seal is primary failure. Shaft surface has minor scoring but within limits.",
        ],
        "Housing Casting": [
            "Replaced SGB-6500. Housing Casting has internal porosity causing pressure loss. Power steering effort increased. External housing shows weeping at casting seam. Cannot repair, replacement required.",
            "SGB-6500 replaced. Housing Casting cracked at mounting ear. Stress crack from frame flex. Gearbox loose on frame causing clunking and increased steering effort.",
        ],
        "Spool Valve": [
            "Replaced SGB-6500. Spool Valve sticking causing groaning noise during turns. Valve spool has scoring marks. Contamination in hydraulic fluid scratched valve bore. Flow control erratic.",
        ],
        "Hydraulic Fitting Set": [
            "SGB-6500 replaced. Hydraulic Fitting Set pressure line fitting cracked. Slow fluid loss causing intermittent hard steering. Found fluid puddle at fitting. O-ring also deteriorated. Fitting replacement attempted but threads damaged.",
        ],
        "Pitman Arm": [
            "Replaced SGB-6500. Pitman Arm spline connection to Sector Shaft has loosened. Clunking felt in steering on direction changes. Arm retorqued but play returned. Spline interface worn on Pitman Arm.",
        ],
    },
}

CLAIM_DIST = {
    "TC-5000": 150,
    "TCM-3200": 120,
    "ACM-2800": 100,
    "EXM-4100": 70,
    "SGB-6500": 60,
}

BAD_BATCH_CLAIM_RATES = {
    "TC-5000":  0.55,
    "TCM-3200": 0.75,
}

SUB_PART_WEIGHTS_BAD_BATCH = {
    "TC-5000":  {"VGT Actuator": 50, "VGT Actuator_cascade": 8, "Turbine Wheel": 12, "Bearing Housing": 10, "Compressor Wheel": 7, "Wastegate Valve": 6, "Oil Feed Line": 4, "Heat Shield": 3},
    "TCM-3200": {"Main PCB": 48, "Main PCB_cascade": 8, "Solenoid Pack": 12, "Wiring Harness": 10, "Connector Housing": 8, "Pressure Transducer": 6, "Temperature Sensor": 4, "Firmware Chip": 4},
    "ACM-2800": {"Piston and Cylinder Kit": 45, "Piston and Cylinder Kit_cascade": 8, "Governor": 13, "Compressor Head": 12, "Unloader Valve": 7, "Intake Filter": 5, "Discharge Line Assembly": 5, "Air Dryer Interface Gasket": 5},
}

SUB_PART_WEIGHTS_NORMAL = {
    "TC-5000":  {"VGT Actuator": 8, "Turbine Wheel": 20, "Bearing Housing": 18, "Compressor Wheel": 16, "Wastegate Valve": 15, "Oil Feed Line": 12, "Heat Shield": 11},
    "TCM-3200": {"Main PCB": 8, "Solenoid Pack": 20, "Wiring Harness": 16, "Connector Housing": 15, "Pressure Transducer": 15, "Temperature Sensor": 14, "Firmware Chip": 12},
    "EXM-4100": {"Heat Shield": 18, "Heat Shield_cascade": 4, "Gasket Set": 20, "Manifold Casting": 16, "EGR Port Insert": 13, "Mounting Stud Kit": 11, "Expansion Joint": 10, "Pyrometer Boss": 8},
    "ACM-2800": {"Piston and Cylinder Kit": 40, "Piston and Cylinder Kit_cascade": 8, "Governor": 13, "Compressor Head": 12, "Unloader Valve": 8, "Intake Filter": 6, "Discharge Line Assembly": 7, "Air Dryer Interface Gasket": 6},
    "SGB-6500": {"Sector Shaft": 18, "Sector Shaft_cascade": 4, "Piston and Rack Assembly": 20, "Input Shaft Seal": 18, "Housing Casting": 16, "Spool Valve": 10, "Hydraulic Fitting Set": 8, "Pitman Arm": 6},
}

COMPLAINT_PREFIXES = [
    "", "", "",
    "Driver reports ",
    "Customer says ",
    "Operator called in saying ",
    "Driver brought truck in, ",
    "Customer complaint: ",
    "Fleet manager called, driver says ",
    "Repeat visit. ",
    "Driver pulled off highway, ",
    "Brought in on tow, ",
    "Came in for PM, driver mentioned ",
    "Driver refused load, says ",
    "Called from truck stop, ",
    "Road call. ",
    "Second time this month. ",
    "Fleet down, ",
    "Driver says since last service ",
    "New driver on this truck reports ",
]

COMPLAINT_SUFFIXES = [
    "", "", "", "",
    ". Truck has {miles}k miles.",
    ". Been like this for about a week.",
    ". Getting worse every day.",
    ". Happened twice today.",
    ". First noticed it yesterday.",
    ". Only happens when loaded.",
    ". Worse in cold weather.",
    ". Worse when hot outside.",
    ". Started after fueling up.",
    ". Truck was fine last month.",
    ". Other trucks in fleet don't do this.",
    ". Can't keep running like this.",
    ". Need this truck back ASAP.",
    ". Driver wants a different truck.",
    ". Happened on I-90 westbound.",
    ". Third driver to complain about this unit.",
]

def vary_complaint(complaint, mileage):
    prefix = random.choice(COMPLAINT_PREFIXES)
    suffix = random.choice(COMPLAINT_SUFFIXES)
    if prefix and complaint[0].isupper():
        complaint = complaint[0].lower() + complaint[1:]
    result = prefix + complaint
    if suffix:
        result += suffix.format(miles=mileage // 1000)
    return result

def weighted_choice(weights_dict):
    items = list(weights_dict.keys())
    weights = list(weights_dict.values())
    return random.choices(items, weights=weights, k=1)[0]

def pick_serial(part_number, need_bad_batch):
    pool = parts_by_pn[part_number]
    if need_bad_batch:
        bad_pool = [p for p in pool if has_bad_batch(p)]
        if bad_pool:
            return random.choice(bad_pool)
    good_pool = [p for p in pool if not has_bad_batch(p)]
    if good_pool:
        return random.choice(good_pool)
    return random.choice(pool)

def pick_serial_any_supplier(part_number):
    return random.choice(parts_by_pn[part_number])

claims = []
claim_counter = 0
complaint_usage = {}

for part_number, total_claims in CLAIM_DIST.items():
    bad_batch_rate = BAD_BATCH_CLAIM_RATES.get(part_number, 0)
    n_bad = int(total_claims * bad_batch_rate) if part_number in BAD_BATCH_IDS else 0
    n_normal = total_claims - n_bad

    for i in range(total_claims):
        claim_counter += 1
        claim_id = f"WC-2024-{claim_counter:05d}"

        is_bad_batch_claim = i < n_bad
        if part_number in DESIGN_PROBLEM_PARTS:
            part = pick_serial_any_supplier(part_number)
        else:
            part = pick_serial(part_number, is_bad_batch_claim)

        if is_bad_batch_claim and part_number in SUB_PART_WEIGHTS_BAD_BATCH:
            sub_part_key = weighted_choice(SUB_PART_WEIGHTS_BAD_BATCH[part_number])
        else:
            sub_part_key = weighted_choice(SUB_PART_WEIGHTS_NORMAL[part_number])

        complaint_key = sub_part_key.replace("_cascade", "")
        complaint_list = CUSTOMER_COMPLAINTS[part_number].get(complaint_key, ["General complaint about the unit"])
        usage_key = (part_number, complaint_key)
        used = complaint_usage.get(usage_key, set())
        available = [c for i_c, c in enumerate(complaint_list) if i_c not in used]
        if not available:
            complaint_usage[usage_key] = set()
            available = complaint_list
            used = set()
        idx = complaint_list.index(random.choice(available))
        used.add(idx)
        complaint_usage[usage_key] = used
        mileage_at_claim = random.randint(45000, 650000)
        customer_complaint = vary_complaint(complaint_list[idx], mileage_at_claim)

        tech_list = TECH_NOTES_TEMPLATES[part_number].get(sub_part_key, 
            TECH_NOTES_TEMPLATES[part_number].get(complaint_key, [f"Replaced {part_number}. Found {complaint_key} failure."]))
        technician_notes = random.choice(tech_list)

        mfg_date = datetime.strptime(part["manufacture_date"], "%Y-%m-%d")
        min_claim_date = mfg_date + timedelta(days=random.randint(30, 180))
        max_claim_date = min(min_claim_date + timedelta(days=random.randint(60, 365)), datetime(2025, 12, 31))
        if max_claim_date <= min_claim_date:
            max_claim_date = min_claim_date + timedelta(days=30)
        claim_date = min_claim_date + timedelta(days=random.randint(0, (max_claim_date - min_claim_date).days))

        claims.append({
            "claim_id": claim_id,
            "serial_number": part["serial_number"],
            "part_number": part_number,
            "claim_date": claim_date.strftime("%Y-%m-%d"),
            "mileage": mileage_at_claim,
            "dealer_id": random.choice(DEALERS),
            "customer_complaint": customer_complaint,
            "technician_notes": technician_notes,
        })

random.shuffle(claims)

with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "claim_id", "serial_number", "part_number", "claim_date", 
        "mileage", "dealer_id", "customer_complaint", "technician_notes"
    ])
    writer.writeheader()
    writer.writerows(claims)

print(f"Generated {len(claims)} warranty claims to {OUTPUT_CSV}")

print("\nClaims by part:")
from collections import Counter
pn_counts = Counter(c["part_number"] for c in claims)
for pn, cnt in sorted(pn_counts.items()):
    print(f"  {pn}: {cnt}")

print("\nSample claims:")
for c in claims[:3]:
    print(f"\n  {c['claim_id']} | {c['part_number']} | {c['serial_number']}")
    print(f"  Complaint: {c['customer_complaint']}")
    print(f"  Tech Notes: {c['technician_notes'][:120]}...")
