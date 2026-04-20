import os
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "docs")
SCHEMATIC_DIR = os.path.join(BASE_DIR, "data", "docs", "schematics")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SCHEMATIC_DIR, exist_ok=True)


class PartManualPDF(FPDF):
    def __init__(self, part_number, part_name):
        super().__init__()
        self.part_number = part_number
        self.part_name = part_name

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 5, f"TITAN MOTORS OEM Part Manual | {self.part_number}", align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 4, "Distribution: Authorized Dealer Service Departments Only", align="L", new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.cell(0, 10, f"TITAN MOTORS Confidential | {self.part_number} Rev C | Page {self.page_no()}/{{nb}}", align="C")

    def add_cover(self, title, subtitle, revision, date):
        self.add_page()
        self.ln(25)
        self.set_font("Helvetica", "B", 24)
        self.multi_cell(0, 12, title, align="C")
        self.ln(5)
        self.set_font("Helvetica", "", 14)
        self.multi_cell(0, 8, subtitle, align="C")
        self.ln(12)
        self.set_font("Helvetica", "", 11)
        for line in [
            f"Part Number: {self.part_number}",
            f"Revision: {revision}",
            f"Date: {date}",
            "Classification: Dealer Restricted",
            "Supersedes: All previous revisions",
        ]:
            self.cell(0, 7, line, align="C", new_x="LMARGIN", new_y="NEXT")

    def add_section(self, number, title):
        self.add_page()
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, f"Section {number}: {title}", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def add_subsection(self, title):
        self.ln(3)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def add_body(self, text):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def add_spec_row(self, label, value):
        self.set_font("Helvetica", "B", 9)
        self.cell(70, 6, label, border=1)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, value, border=1, new_x="LMARGIN", new_y="NEXT")

    def add_component_table(self, components):
        col_widths = [10, 45, 135]
        line_h = 5
        self.set_font("Helvetica", "B", 9)
        headers = ["Item", "Sub-Component", "Description"]
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, align="C")
        self.ln()
        self.set_font("Helvetica", "", 8)
        for idx, (name, desc) in enumerate(components, 1):
            x_start = self.get_x()
            y_start = self.get_y()
            self.set_xy(x_start + col_widths[0] + col_widths[1], y_start)
            self.multi_cell(col_widths[2], line_h, desc)
            row_h = max(self.get_y() - y_start, line_h)
            self.set_xy(x_start, y_start)
            self.cell(col_widths[0], row_h, str(idx), border=1, align="C")
            self.cell(col_widths[1], row_h, name, border=1)
            desc_x = self.get_x()
            self.set_xy(desc_x, y_start)
            self.multi_cell(col_widths[2], line_h, desc, border=1)
            self.set_xy(x_start, y_start + row_h)

    def add_schematic(self, image_path, caption=""):
        if os.path.exists(image_path):
            avail_w = self.w - self.l_margin - self.r_margin
            self.image(image_path, x=self.l_margin, w=avail_w)
            self.ln(3)
            if caption:
                self.set_font("Helvetica", "I", 9)
                self.cell(0, 5, caption, align="C", new_x="LMARGIN", new_y="NEXT")
                self.ln(4)
        else:
            self.set_font("Helvetica", "I", 10)
            self.cell(0, 8, f"[Schematic: {os.path.basename(image_path)} - not found]", align="C", new_x="LMARGIN", new_y="NEXT")
            self.ln(4)


# ---------------------------------------------------------------------------
# TC-5000 Turbocharger Assembly
# ---------------------------------------------------------------------------
def build_turbocharger_manual():
    pdf = PartManualPDF("TC-5000", "Turbocharger Assembly")
    pdf.alias_nb_pages()

    pdf.add_cover(
        "Turbocharger Assembly",
        "Service and Diagnostic Manual\nTITAN MOTORS MX-13 Engine Platform",
        "C", "January 2025"
    )

    # Section 1 - General Description
    pdf.add_section("1", "General Description")
    pdf.add_body(
        "The TC-5000 Turbocharger Assembly is a variable geometry turbocharger designed for the "
        "TITAN MOTORS MX-13 engine platform used in Atlas T680, T880, W990, and Titan 579, 567 "
        "model families. The assembly provides forced induction across the full engine operating "
        "range and is integral to meeting current EPA emissions requirements through precise "
        "management of exhaust energy and air-fuel ratio control."
    )
    pdf.add_body(
        "This manual covers the complete service lifecycle of the TC-5000 assembly including "
        "installation, theory of operation, diagnostic procedures, and preventive maintenance "
        "guidance. Technicians should be familiar with OEM diagnostic diagnostic software operation and "
        "TITAN MOTORS MX-13 engine fundamentals before performing work on the turbocharger system."
    )

    # Section 2 - Components
    pdf.add_section("2", "Component Identification")
    pdf.add_body(
        "The TC-5000 consists of seven major sub-component groups illustrated in Figure 2-1 below. "
        "Each component is identified by item number and described in Table 2-1."
    )
    schematic_path = os.path.join(SCHEMATIC_DIR, "Turbocharger_Assembly_Schematic.png")
    pdf.add_schematic(schematic_path, "Figure 2-1: TC-5000 Turbocharger Assembly - Exploded View")

    pdf.add_subsection("Table 2-1: Sub-Component Identification")
    pdf.add_component_table([
        ("Turbine Wheel",
         "Inconel 713C investment casting. Converts exhaust gas thermal energy into rotational force. "
         "Rated to 128,000 RPM and 1,250 deg F continuous duty."),
        ("Compressor Wheel",
         "Machined 2618-T61 aluminum alloy. Draws ambient air through the intake and delivers "
         "compressed charge air at 18-42 PSI boost to the intercooler circuit."),
        ("Bearing Housing",
         "Central structural member containing the full-floating hydrodynamic journal bearing, "
         "oil feed and drain passages, and piston ring shaft seals."),
        ("VGT Actuator",
         "Electronically controlled stepper-motor actuator. Modulates the turbine vane ring position "
         "to control exhaust gas velocity across the turbine wheel. Response time < 120 ms."),
        ("Wastegate Valve",
         "Spring-loaded bypass valve. Diverts exhaust gas around the turbine when boost pressure "
         "exceeds 48 +/- 2 PSI crack pressure to prevent over-boost."),
        ("Oil Feed Line",
         "Braided stainless steel line with restrictor orifice. Delivers filtered engine oil to the "
         "bearing housing at 22-65 PSI depending on engine speed."),
        ("Heat Shield",
         "Stamped stainless steel thermal barrier. Isolates turbine housing radiant heat from "
         "adjacent wiring harnesses, hoses, and engine-bay components."),
    ])

    # Section 3 - Specifications
    pdf.add_section("3", "Specifications")
    pdf.add_body("The following specifications apply to all TC-5000 variants unless noted otherwise.")
    for label, value in [
        ("Maximum Turbine Speed", "128,000 RPM"),
        ("Boost Pressure Range (sea level)", "18 - 42 PSI"),
        ("VGT Actuator Response Time", "< 120 ms commanded to achieved"),
        ("Oil Feed Pressure (at idle)", "22 - 35 PSI"),
        ("Oil Feed Pressure (at rated)", "45 - 65 PSI"),
        ("Exhaust Gas Temperature (max continuous)", "1,250 deg F"),
        ("Turbine Housing Material", "High-silicon ductile iron"),
        ("Bearing Type", "Full-floating journal bearing"),
        ("Wastegate Crack Pressure", "48 +/- 2 PSI"),
        ("Assembly Weight (dry)", "47.5 lbs"),
        ("Mounting Bolt Torque (V-band clamp)", "11.5 ft-lbs"),
        ("Oil Feed Line Fitting Torque", "18 ft-lbs"),
        ("Oil Drain Line Fitting Torque", "22 ft-lbs"),
        ("Coolant Supply Line (if equipped)", "15 ft-lbs"),
    ]:
        pdf.add_spec_row(label, value)

    # Section 4 - Installation and Removal
    pdf.add_section("4", "Installation and Removal")
    pdf.add_subsection("Removal Procedure")
    pdf.add_body(
        "Prior to removal, allow the engine to cool for a minimum of 45 minutes. The turbine "
        "housing surface temperature can exceed 800 degrees F during operation and will retain "
        "significant heat for an extended period. Disconnect the battery ground cables before "
        "beginning work."
    )
    pdf.add_body(
        "Begin by removing the charge air cooler pipe from the compressor outlet. Loosen the "
        "V-band clamp using a 10mm socket and carefully separate the joint. Cap the compressor "
        "outlet to prevent foreign object entry. Next, disconnect the oil feed line at the "
        "bearing housing fitting using a 14mm line wrench. Allow residual oil to drain into a "
        "suitable container. Disconnect the oil drain line at the lower bearing housing flange. "
        "Remove the four M8 bolts securing the oil drain flange and lower the drain tube clear "
        "of the assembly."
    )
    pdf.add_body(
        "Disconnect the VGT actuator electrical connector by depressing the locking tab and "
        "pulling straight back. Do not pry on the connector body. Disconnect the wastegate "
        "actuator vacuum line by pressing the quick-connect release collar."
    )
    pdf.add_body(
        "Remove the exhaust inlet V-band clamp at the turbine housing using a 12mm socket. "
        "The turbocharger can now be lifted free from the exhaust manifold studs. The "
        "assembly weighs approximately 47.5 pounds and requires two-hand support during removal."
    )
    pdf.add_subsection("Installation Procedure")
    pdf.add_body(
        "Inspect the exhaust manifold flange surface for warpage using a straight edge and feeler "
        "gauge set. Maximum allowable deviation is 0.006 inches. Install a new turbine inlet "
        "gasket. Pre-lubricate the bearing housing with 30ml of clean 15W-40 engine oil through "
        "the oil feed port before mounting the assembly."
    )
    pdf.add_body(
        "Position the turbocharger on the exhaust manifold studs and hand-tighten the V-band "
        "clamp. Torque the V-band clamp to 11.5 ft-lbs. Reconnect the oil feed line (18 ft-lbs), "
        "oil drain line (22 ft-lbs), VGT actuator connector, wastegate vacuum line, charge air "
        "cooler pipe, and inlet hose."
    )

    # Section 5 - Theory of Operation
    pdf.add_section("5", "Theory of Operation")
    pdf.add_subsection("Variable Geometry Turbocharging")
    pdf.add_body(
        "The TC-5000 employs a variable geometry turbine to provide optimal boost pressure across "
        "the entire engine operating range. At low engine speeds, the ECM commands the VGT actuator "
        "to close the vane ring, reducing the effective nozzle area and increasing exhaust gas "
        "velocity across the turbine wheel. As engine speed and exhaust flow increase, the actuator "
        "progressively opens the vane ring to prevent over-boosting."
    )
    pdf.add_subsection("Bearing System Dynamics")
    pdf.add_body(
        "The bearing housing supports the turbocharger shaft at rotational speeds exceeding "
        "120,000 RPM through a full-floating hydrodynamic journal bearing. This bearing type "
        "relies entirely on a pressurized oil film to prevent metal-to-metal contact. The oil "
        "film thickness at rated speed is approximately 0.0015 inches."
    )
    pdf.add_subsection("Wastegate Function")
    pdf.add_body(
        "The wastegate valve provides mechanical overpressure protection by diverting exhaust gas "
        "flow around the turbine wheel when boost pressure exceeds the crack pressure setting. "
        "The valve is spring-loaded to the closed position and opens progressively as boost "
        "pressure acts on the actuator diaphragm."
    )

    # Section 6 - Troubleshooting and Diagnostics
    pdf.add_section("6", "Troubleshooting and Diagnostics")
    pdf.add_body(
        "This section describes common failure symptoms, their probable root causes, and the "
        "recommended diagnostic approach. Technicians should use this information in conjunction "
        "with OEM diagnostic diagnostic software to isolate faults."
    )

    pdf.add_subsection("6.1 Gradual Loss of Boost Pressure")
    pdf.add_body(
        "Operators may report a gradual decline in engine pulling power accompanied by dark gray "
        "or black exhaust smoke under load. This condition often develops slowly over thousands of "
        "miles, making it difficult to identify when it began. The most common cause of gradual "
        "boost loss is degradation of the wastegate valve seat. Over extended service, the "
        "wastegate valve seat erodes from the high-velocity, high-temperature exhaust gas that "
        "contacts the sealing surface each time the valve cycles. As the seat erodes, the "
        "wastegate fails to fully seal at pressures below its crack point, allowing exhaust "
        "energy to bypass the turbine wheel continuously. Drivers in flat terrain may not notice "
        "the reduced boost, but operators who regularly encounter mountain grades or operate at "
        "altitude will report that the truck lacks the pulling power it once had, particularly "
        "above 6,000 feet elevation."
    )
    pdf.add_body(
        "If wastegate seat erosion is ruled out, attention should turn to the VGT actuator. "
        "Carbon buildup on the internal vane ring can increase actuator resistance, preventing "
        "the vane ring from closing fully at low engine speeds. Perform a VGT actuator sweep "
        "test through OEM diagnostic. The actuator should move smoothly from 0 to 100 percent position "
        "with no hesitation. Monitor current draw during the sweep: normal range is 0.4 to 1.8 "
        "amps. Current spikes above 2.5 amps indicate excessive mechanical resistance from "
        "carbon deposits on the vane ring or degradation of the actuator internal gear mechanism."
    )

    pdf.add_subsection("6.2 Abnormal Turbocharger Noise")
    pdf.add_body(
        "A high-pitched continuous metallic whine from the turbocharger center section, "
        "particularly noticeable at idle and low-speed operation, suggests bearing distress in "
        "the bearing housing. This sound occurs when the oil film supporting the shaft journal "
        "has been compromised, allowing intermittent metal-to-metal contact. The most frequent "
        "cause of oil film disruption is restricted flow through the oil feed line. Over "
        "extended service life, the oil feed line develops internal varnish buildup that "
        "reduces oil flow to the bearing housing below the minimum required to maintain a full "
        "hydrodynamic film. The whine may initially appear only during cold starts when oil "
        "viscosity is highest, leading technicians to dismiss it as a temporary condition. If "
        "the oil feed line is not replaced within approximately 8,000 to 10,000 miles of "
        "initial symptom appearance, the bearing sleeve will develop scoring that requires "
        "replacement of the entire bearing housing assembly."
    )
    pdf.add_body(
        "A warbling or oscillating tone that varies independent of engine load indicates that "
        "the turbine wheel balance has been disturbed. This can result from foreign object "
        "damage to the turbine blades, erosion from prolonged exposure to elevated exhaust gas "
        "temperatures, or from the turbine wheel contacting the housing due to excessive shaft "
        "play from bearing wear. Measure shaft end-play using a dial indicator through the oil "
        "drain port. Maximum allowable end-play is 0.003 inches."
    )

    pdf.add_subsection("6.3 Oil in Charge Air System")
    pdf.add_body(
        "The presence of engine oil pooling or dripping at the charge air cooler connections "
        "downstream of the compressor indicates a compressor-side seal failure in the bearing "
        "housing. The compressor wheel piston ring seal prevents engine oil that lubricates the "
        "bearing from migrating along the shaft into the compressor housing. Seal failure is "
        "often secondary to bearing wear that allows excessive shaft radial movement, distorting "
        "the seal contact surface. Inspect the compressor wheel for rub marks on blade tips "
        "which would confirm bearing-related shaft displacement."
    )

    pdf.add_subsection("6.4 Intermittent Power Lag During Acceleration")
    pdf.add_body(
        "A subtle increase in turbo lag during acceleration events, most noticeable when the "
        "driver tips in the throttle from idle or low cruise RPM, is the earliest indicator "
        "of VGT actuator degradation. The actuator develops increased internal resistance "
        "typically due to carbon infiltration past the housing seals or wear in the internal "
        "gear mechanism. At this stage the ECM may not log a fault code because the actuator "
        "still achieves commanded position - it simply takes longer to get there. The operator "
        "may describe it as the truck feeling sluggish on some days but not others. If not "
        "addressed within approximately 15,000 miles, the degradation forces the ECM to "
        "compensate by modifying fueling strategy, increasing exhaust gas temperatures by 50 "
        "to 100 degrees F above normal range, which accelerates thermal fatigue in the turbine "
        "wheel at the blade root fillets."
    )

    pdf.add_subsection("6.5 Heat Shield Failure Effects")
    pdf.add_body(
        "A cracked, warped, or loose heat shield allows radiant thermal energy from the turbine "
        "housing to reach adjacent engine bay components that are not designed for high-temperature "
        "exposure. The most common secondary damage is degradation of wiring harness insulation "
        "and softening of rubber coolant hoses in the immediate vicinity. If a vehicle presents "
        "with unexplained sensor faults or coolant leaks near the top of the engine between the "
        "manifold and valve cover, inspect the heat shield condition before beginning electrical "
        "or cooling system diagnosis."
    )

    # Section 7 - Preventive Maintenance
    pdf.add_section("7", "Preventive Maintenance")
    pdf.add_body(
        "At each B-service interval (50,000 miles), visually inspect all external connections "
        "and mounting hardware. Check V-band clamp torque at the turbine inlet and compressor "
        "outlet. Inspect the VGT actuator electrical connector for heat damage or corrosion. "
        "Verify that the heat shield is securely mounted and has not developed cracks or warpage."
    )
    pdf.add_body(
        "At each C-service interval (100,000 miles), perform a VGT actuator sweep test using "
        "OEM diagnostic and record actuator response time and current draw. Compare to previous service "
        "records to identify trending degradation. Inspect the oil feed line external surface "
        "for cracking, chafing, or deformation."
    )
    pdf.add_body(
        "At 200,000 miles, regardless of symptom status, TITAN MOTORS recommends replacement of the "
        "oil feed line assembly as a preventive measure. Field data shows that oil feed lines "
        "in service beyond 200,000 miles have a significantly elevated risk of internal varnish "
        "restriction."
    )

    filename = "PM_TC-5000_Turbocharger_Assembly.pdf"
    path = os.path.join(OUTPUT_DIR, filename)
    pdf.output(path)
    print(f"  {filename} ({pdf.page_no()} pages)")


# ---------------------------------------------------------------------------
# TCM-3200 Transmission Control Module
# ---------------------------------------------------------------------------
def build_tcm_manual():
    pdf = PartManualPDF("TCM-3200", "Transmission Control Module")
    pdf.alias_nb_pages()

    pdf.add_cover(
        "Transmission Control Module",
        "Service and Diagnostic Manual\nTITAN MOTORS TX-18 Pro Automated Transmission",
        "C", "January 2025"
    )

    # Section 1
    pdf.add_section("1", "General Description")
    pdf.add_body(
        "The TCM-3200 Transmission Control Module is the electronic brain of the TITAN MOTORS TX-18 Pro "
        "automated manual transmission used in Atlas and Titan Class 8 vehicles. The module "
        "integrates sensor inputs, driver commands, and powertrain data to execute precise gear "
        "selection, clutch engagement, and shift quality optimization in real time."
    )

    # Section 2 - Components
    pdf.add_section("2", "Component Identification")
    pdf.add_body(
        "The TCM-3200 assembly comprises seven sub-component groups described in Table 2-1."
    )
    schematic_path = os.path.join(SCHEMATIC_DIR, "Transmission_Control_Module_Schematic.png")
    pdf.add_schematic(schematic_path, "Figure 2-1: TCM-3200 Transmission Control Module - Component Layout")

    pdf.add_subsection("Table 2-1: Sub-Component Identification")
    pdf.add_component_table([
        ("Main PCB",
         "Primary processing board with solenoid driver ICs, power management circuitry, and "
         "CAN bus transceivers. Contains all control logic and diagnostic monitoring."),
        ("Solenoid Pack",
         "8-channel proportional solenoid assembly. Converts electronic shift commands into "
         "hydraulic actuator movements via PWM-controlled valve positioning at 400 Hz."),
        ("Wiring Harness",
         "Shielded multi-conductor harness connecting TCM to vehicle CAN bus, ECM data link, "
         "range selector, and instrument cluster. Routes along the transmission tunnel."),
        ("Connector Housing",
         "Deutsch HD36-24-31ST 31-pin sealed connector. IP67-rated environmental seal providing "
         "moisture and contaminant exclusion at the vehicle interface."),
        ("Firmware Chip",
         "Removable EEPROM module storing shift calibration maps, adaptive learning parameters, "
         "and vehicle-specific configuration. Version-matched to ECM software level."),
        ("Pressure Transducer",
         "0-350 PSI strain-gauge sensor monitoring main line hydraulic pressure. Accuracy "
         "+/- 1.5 PSI. Critical for clutch engagement force calculation."),
        ("Temperature Sensor",
         "NTC thermistor measuring transmission fluid temperature at the TCM inlet port. "
         "Range -40 to +300 deg F. Used for viscosity compensation in shift algorithms."),
    ])

    # Section 3 - Specifications
    pdf.add_section("3", "Specifications")
    pdf.add_body("The following specifications apply to all TCM-3200 configurations.")
    for label, value in [
        ("Operating Voltage", "9.0 - 16.0 VDC (nominal 13.8 VDC)"),
        ("Maximum Current Draw", "18A peak during shift event"),
        ("Quiescent Current", "< 35 mA (sleep mode)"),
        ("Communication Protocol", "SAE J1939 CAN Bus, 250 kbps / 500 kbps"),
        ("Operating Temperature Range", "-40 deg F to +250 deg F"),
        ("Solenoid Pack Channels", "8 independent proportional solenoids"),
        ("Pressure Transducer Range", "0 - 350 PSI, +/- 1.5 PSI accuracy"),
        ("Temperature Sensor Range", "-40 deg F to +300 deg F"),
        ("IP Rating", "IP67 (sealed assembly)"),
        ("Connector Type", "Deutsch HD36-24-31ST (31-pin sealed)"),
        ("Assembly Weight", "8.2 lbs"),
        ("Mounting Bolt Torque", "18 ft-lbs (M10 flange bolts)"),
    ]:
        pdf.add_spec_row(label, value)

    # Section 4 - Installation and Removal
    pdf.add_section("4", "Installation and Removal")
    pdf.add_body(
        "The TCM-3200 is mounted on the left side of the transmission housing. Place the "
        "transmission in neutral and apply the parking brake. Disconnect battery ground cables. "
        "The connector uses a secondary locking mechanism that must be disengaged before the "
        "primary latch can be released. Remove the three M10 mounting bolts. During installation "
        "of a new TCM, verify firmware chip version compatibility with the vehicle ECM software "
        "level. After installation, the TCM requires a clutch teach-in procedure and shift "
        "adaptation reset performed through OEM diagnostic."
    )

    # Section 5 - Theory of Operation
    pdf.add_section("5", "Theory of Operation")
    pdf.add_subsection("Shift Execution Process")
    pdf.add_body(
        "The TCM continuously evaluates vehicle speed, engine speed, throttle position, "
        "transmission fluid temperature, and grade sensor data to determine optimal shift points. "
        "When a shift decision is made, the TCM executes a precisely choreographed sequence of "
        "solenoid activations. The entire shift sequence completes in 400 to 800 milliseconds."
    )
    pdf.add_subsection("Adaptive Learning")
    pdf.add_body(
        "The firmware chip stores adaptive learning parameters accumulated over thousands of shift "
        "events. These parameters compensate for normal wear in clutch friction surfaces, "
        "synchronizer ring contact patterns, and fluid viscosity changes. When the firmware chip "
        "is replaced, all adaptive data resets to factory defaults and requires approximately "
        "50 miles of mixed driving to relearn."
    )

    # Section 6 - Troubleshooting and Diagnostics
    pdf.add_section("6", "Troubleshooting and Diagnostics")

    pdf.add_subsection("6.1 Intermittent Shift Faults")
    pdf.add_body(
        "A pattern of intermittent shift faults concentrated in specific gear transitions, "
        "particularly third-to-fourth and sixth-to-seventh where solenoid modulation demands are "
        "highest, often points to degradation of solder joints on the main PCB. The tin-lead "
        "solder connections between the PCB traces and the solenoid driver ICs are subject to "
        "thermal cycling stress as the TCM heats and cools with each drive cycle. Over time, "
        "microscopic cracks develop in the solder fillets, creating intermittent high-resistance "
        "connections that disrupt the precise current ramps needed for smooth solenoid control. "
        "The fault may present as a harsh engagement, a momentary neutral condition between gears, "
        "or a brief activation of the transmission fault lamp that clears on its own."
    )
    pdf.add_body(
        "Confirm main PCB solder joint degradation by performing a controlled thermal test. With "
        "OEM diagnostic monitoring solenoid current waveforms, use a heat gun to raise the TCM housing "
        "temperature to 180 degrees F while monitoring for current waveform distortion. If the "
        "solder joints are compromised, thermal expansion will open the cracked joints, causing "
        "visible current spikes or dropouts."
    )

    pdf.add_subsection("6.2 Communication Loss and Limp Mode")
    pdf.add_body(
        "Complete loss of communication between the TCM and the vehicle CAN bus results in "
        "immediate limp-mode activation. If the loss is intermittent - described by drivers as "
        "the truck randomly entering limp mode for a few seconds then resuming - the most common "
        "cause is degradation of the connector housing seal allowing moisture ingress to the CAN "
        "bus communication pins. Even minor pin corrosion can cause intermittent signal reflection "
        "on the CAN bus that appears to the ECM as a lost node. Inspect the 31-pin connector "
        "for green oxidation on pin surfaces or moisture tracking between pins."
    )
    pdf.add_body(
        "If the connector appears clean, investigate the wiring harness between the TCM and the "
        "vehicle CAN bus junction. The harness routes along the transmission tunnel where it is "
        "exposed to heat, vibration, and potential contact with moving driveline components. "
        "Perform a continuity check with the harness flexed through its full range. An "
        "intermittent break will show as fluctuating resistance during flexing, particularly at "
        "the harness exit point from the connector body where bending loads concentrate."
    )

    pdf.add_subsection("6.3 Erratic Shift Quality")
    pdf.add_body(
        "If the transmission feels different on each shift - sometimes smooth, sometimes jerky, "
        "with no apparent pattern - the most likely cause is erratic readings from the pressure "
        "transducer. The transducer provides main line pressure data critical for clutch "
        "engagement force calculation. If it provides erratic readings, the TCM cannot accurately "
        "predict clutch torque capacity. Compare transducer readings to a calibrated external "
        "pressure gauge installed at the main line test port. A deviation exceeding 8 PSI "
        "indicates transducer failure."
    )

    pdf.add_subsection("6.4 Temperature-Related Shift Complaints")
    pdf.add_body(
        "Shifts that feel unusually harsh in warm weather or sluggish and dragging in cold "
        "conditions even after the vehicle has been operating long enough for the fluid to reach "
        "normal temperature indicate a faulty temperature sensor. Inaccurate temperature sensor "
        "readings cause the TCM to apply incorrect viscosity compensation to its shift algorithms. "
        "Verify sensor accuracy by comparing TCM-reported fluid temperature to a contact "
        "thermometer reading at the transmission housing after a 30-minute highway drive."
    )

    pdf.add_subsection("6.5 Delayed Gear Engagement")
    pdf.add_body(
        "A noticeable pause between selecting a gear and feeling the transmission engage, "
        "combined with earlier intermittent shift fault history, indicates that the solenoid pack "
        "has sustained secondary damage from the main PCB solder joint cascade. The erratic "
        "current from cracked solder joints causes impact loads on the solenoid valve seats, "
        "which develop wear patterns preventing proper sealing. Hydraulic pressure bleeds past "
        "the worn valve seats, creating the engagement delay. If both intermittent shift faults "
        "and delayed engagement have been present for more than 3,000 miles, replacement of the "
        "complete TCM assembly is required."
    )

    # Section 7
    pdf.add_section("7", "Preventive Maintenance")
    pdf.add_body(
        "At each B-service interval, inspect the 31-pin connector housing for moisture or "
        "corrosion. Apply dielectric grease to connector pins in salt-exposure or coastal "
        "environments. Verify mounting bolt torque at 18 ft-lbs and grounding strap integrity. "
        "Inspect wiring harness routing for clearance from exhaust and driveshaft."
    )
    pdf.add_body(
        "At each C-service interval, connect OEM diagnostic and perform a solenoid electrical health "
        "check. Record the resistance of each solenoid channel and compare to previous records. "
        "A resistance drift exceeding 0.5 ohms from baseline may indicate early coil degradation."
    )

    filename = "PM_TCM-3200_Transmission_Control_Module.pdf"
    path = os.path.join(OUTPUT_DIR, filename)
    pdf.output(path)
    print(f"  {filename} ({pdf.page_no()} pages)")


# ---------------------------------------------------------------------------
# EXM-4100 Exhaust Manifold Assembly
# ---------------------------------------------------------------------------
def build_exhaust_manifold_manual():
    pdf = PartManualPDF("EXM-4100", "Exhaust Manifold Assembly")
    pdf.alias_nb_pages()

    pdf.add_cover(
        "Exhaust Manifold Assembly",
        "Service and Diagnostic Manual\nTITAN MOTORS MX-13 / Cummins X15 Engine Platforms",
        "C", "January 2025"
    )

    # Section 1
    pdf.add_section("1", "General Description")
    pdf.add_body(
        "The EXM-4100 Exhaust Manifold Assembly collects exhaust gases from the engine cylinders "
        "and directs them to the turbocharger inlet. The manifold operates continuously at "
        "temperatures exceeding 1,200 degrees Fahrenheit and must withstand severe thermal cycling "
        "over the life of the engine."
    )

    # Section 2 - Components
    pdf.add_section("2", "Component Identification")
    pdf.add_body(
        "The EXM-4100 consists of seven sub-component groups described in Table 2-1."
    )
    schematic_path = os.path.join(SCHEMATIC_DIR, "Exhaust_Manifold_Assembly_Schematic.png")
    pdf.add_schematic(schematic_path, "Figure 2-1: EXM-4100 Exhaust Manifold Assembly - Component Layout")

    pdf.add_subsection("Table 2-1: Sub-Component Identification")
    pdf.add_component_table([
        ("Manifold Casting",
         "High-chromium ductile iron (D5S Ni-Resist) primary structural element. Designed with "
         "controlled wall thickness variations to manage thermal stress distribution."),
        ("Gasket Set",
         "Multi-layer steel (MLS) 3-layer gaskets providing cylinder-head-to-manifold sealing "
         "across six individual port interfaces. Must be replaced at every manifold installation."),
        ("EGR Port Insert",
         "Stainless steel insert at the EGR pickup port. Directs a metered portion of exhaust "
         "gas to the EGR cooler circuit for NOx emissions control."),
        ("Heat Shield",
         "Stamped stainless steel thermal barrier mounted on the cab-side of the manifold. "
         "Prevents radiant heat transfer to the engine wiring harness and cab-side components."),
        ("Mounting Stud Kit",
         "Inconel 718 studs with controlled-stretch design. Secures the manifold to the cylinder "
         "head at 44 ft-lbs torque with anti-seize compound. Quantity: 12 per manifold."),
        ("Expansion Joint",
         "Bellows-type stainless steel flex joint at the manifold-to-turbocharger interface. "
         "Absorbs angular misalignment and differential thermal expansion. Rated 500,000 cycles."),
        ("Pyrometer Boss",
         "Welded M12 x 1.25 threaded boss for EGT sensor mounting. Positioned in the merged "
         "exhaust flow path downstream of the collector for accurate bulk gas measurement."),
    ])

    # Section 3 - Specifications
    pdf.add_section("3", "Specifications")
    pdf.add_body("The following specifications apply to all EXM-4100 configurations.")
    for label, value in [
        ("Material", "High-chromium ductile iron (D5S Ni-Resist)"),
        ("Maximum Continuous Temperature", "1,400 deg F"),
        ("Peak Transient Temperature", "1,600 deg F (< 30 seconds)"),
        ("Mounting Stud Torque", "44 ft-lbs (lubricated threads)"),
        ("Mounting Stud Material", "Inconel 718"),
        ("Gasket Type", "Multi-layer steel (MLS), 3-layer"),
        ("Flex Joint Angular Range", "+/- 2.5 degrees"),
        ("EGT Sensor Boss Thread", "M12 x 1.25"),
        ("Assembly Weight", "68 lbs"),
        ("Flange Flatness Tolerance", "0.004 inches max deviation"),
    ]:
        pdf.add_spec_row(label, value)

    # Section 4 - Installation and Removal
    pdf.add_section("4", "Installation and Removal")
    pdf.add_body(
        "Allow the engine to cool completely before attempting manifold removal. Remove the "
        "turbocharger assembly per the TC-5000 service manual. Disconnect the EGT sensor. "
        "Remove the heat shield mounting bolts. Remove mounting studs using a stud extractor - "
        "do not use pliers on stud threads. During installation, install new gaskets at every "
        "manifold installation, apply anti-seize to stud threads, and torque in the specified "
        "sequence to 44 ft-lbs."
    )

    # Section 5 - Theory of Operation
    pdf.add_section("5", "Theory of Operation")
    pdf.add_subsection("Thermal Management")
    pdf.add_body(
        "During loaded highway operation, exhaust gas temperatures at the manifold ports typically "
        "range from 900 to 1,200 degrees F. During DPF regeneration, temperatures can spike to "
        "1,400 degrees for 20 to 40 minutes. The manifold casting's thermal expansion during a "
        "cold-start-to-full-temperature cycle can exceed 0.040 inches along its length."
    )
    pdf.add_subsection("Expansion Joint Function")
    pdf.add_body(
        "The expansion joint between the manifold outlet flange and the turbocharger inlet "
        "accommodates angular misalignment and absorbs differential thermal expansion. The "
        "bellows element has a rated life of 500,000 thermal cycles."
    )

    # Section 6 - Troubleshooting and Diagnostics
    pdf.add_section("6", "Troubleshooting and Diagnostics")

    pdf.add_subsection("6.1 Exhaust Leak at Cylinder Port")
    pdf.add_body(
        "Exhaust manifold leaks present with a characteristic ticking or tapping sound most "
        "prominent during cold start that diminishes as the engine reaches operating temperature. "
        "This occurs because thermal expansion closes the leak path as the manifold heats. The "
        "sound is rhythmic and synchronized with engine firing order. The most common cause is "
        "degradation of the gasket set at an individual cylinder port, typically at the number "
        "one or number six positions where thermal expansion displacement is greatest. Visible "
        "exhaust staining - a fan-shaped soot deposit on the manifold surface adjacent to the "
        "affected port - confirms the leak location."
    )
    pdf.add_body(
        "If the gasket leak is not addressed within 20,000 to 30,000 miles, the escaping "
        "exhaust gas at 900 to 1,200 degrees F creates a localized hot spot on the manifold "
        "casting, generating thermal fatigue cracking in the casting wall. The mounting stud kit "
        "studs adjacent to the cracked area will develop elongation from uneven loading that "
        "cannot be corrected by re-torquing."
    )

    pdf.add_subsection("6.2 Exhaust Leak at Turbocharger Interface")
    pdf.add_body(
        "A higher-pitched hissing at the manifold-to-turbo connection that does not diminish "
        "with warm-up indicates failure of the expansion joint bellows. When the expansion joint "
        "fatigues, it develops microscopic cracks in the bellows convolutions that initially "
        "allow only trace amounts of exhaust gas to escape. This seepage may produce a faint "
        "exhaust odor in the engine bay detectable only at idle, and is easily confused with "
        "residual exhaust from a parked-idle condition."
    )

    pdf.add_subsection("6.3 Phantom EGT Spikes")
    pdf.add_body(
        "Intermittent spikes in exhaust gas temperature readings that do not correlate with "
        "load changes may indicate a cracked pyrometer boss rather than actual temperature "
        "excursions. The weld joint between the boss and the casting can develop hairline cracks "
        "from thermal cycling, allowing exhaust gas to impinge directly on the sensor element. "
        "These phantom EGT spikes can trigger unnecessary DPF regeneration events, increasing "
        "fuel consumption and accelerating DPF ash loading."
    )

    pdf.add_subsection("6.4 Heat Damage to Adjacent Components")
    pdf.add_body(
        "A damaged or poorly mounted heat shield allows radiant heat from the manifold to reach "
        "components not designed for high-temperature exposure. The most common secondary damage "
        "is degradation of the engine wiring harness insulation on the intake side, resulting "
        "in intermittent electrical faults that appear unrelated to the exhaust system. "
        "Heat discoloration on the cab-side surface of the heat shield - a bronze or purple "
        "tint on what should be a silver metallic surface - indicates thermal over-exposure."
    )

    pdf.add_subsection("6.5 EGR Flow Restriction")
    pdf.add_body(
        "Reduced EGR flow causing elevated NOx readings during emissions testing can result from "
        "carbon buildup in the EGR port insert. The insert's internal passage narrows over time "
        "as exhaust carbon deposits accumulate on the inner walls, restricting the metered flow "
        "to the EGR cooler. This restriction develops gradually and may not trigger an immediate "
        "fault code until the EGR flow deviation exceeds the ECM tolerance threshold."
    )

    # Section 7
    pdf.add_section("7", "Preventive Maintenance")
    pdf.add_body(
        "At each B-service, perform a cold-start listen test for exhaust tick sounds during the "
        "first 60 seconds of engine operation. At each C-service, inspect mounting stud torque - "
        "studs that have lost more than 15 percent of specified torque should be replaced. "
        "Inspect the expansion joint bellows for cracks or exhaust staining. At 300,000 miles, "
        "proactively replace the gasket set and mounting stud kit."
    )

    filename = "PM_EXM-4100_Exhaust_Manifold_Assembly.pdf"
    path = os.path.join(OUTPUT_DIR, filename)
    pdf.output(path)
    print(f"  {filename} ({pdf.page_no()} pages)")


# ---------------------------------------------------------------------------
# ACM-2800 Air Compressor Assembly
# ---------------------------------------------------------------------------
def build_air_compressor_manual():
    pdf = PartManualPDF("ACM-2800", "Air Compressor Assembly")
    pdf.alias_nb_pages()

    pdf.add_cover(
        "Air Compressor Assembly",
        "Service and Diagnostic Manual\nClass 8 Air Brake System Platform",
        "C", "January 2025"
    )

    # Section 1
    pdf.add_section("1", "General Description")
    pdf.add_body(
        "The ACM-2800 Air Compressor Assembly provides the compressed air supply for the "
        "vehicle air brake system, suspension air management, and auxiliary pneumatic accessories. "
        "The compressor is engine-driven through a gear train coupled to the engine timing gears."
    )

    # Section 2 - Components
    pdf.add_section("2", "Component Identification")
    pdf.add_body(
        "The ACM-2800 assembly consists of seven sub-component groups described in Table 2-1."
    )
    schematic_path = os.path.join(SCHEMATIC_DIR, "Air_Compressor_Assembly_Schematic.png")
    pdf.add_schematic(schematic_path, "Figure 2-1: ACM-2800 Air Compressor Assembly - Component Layout")

    pdf.add_subsection("Table 2-1: Sub-Component Identification")
    pdf.add_component_table([
        ("Compressor Head",
         "Upper cylinder enclosure containing the valve plate and reed valves that control "
         "intake and discharge air flow direction during the compression cycle."),
        ("Piston and Cylinder Kit",
         "Primary compression element. Single-cylinder reciprocating assembly with two compression "
         "rings and one oil control ring. Displacement: 18.7 cubic inches per revolution."),
        ("Unloader Valve",
         "Pneumatic valve that holds inlet reed valves open during unloaded operation, preventing "
         "pressure build when system is at cut-out pressure. Controlled by governor signal."),
        ("Governor",
         "Pressure-sensing regulator monitoring system air pressure via wet tank sensing line. "
         "Signals unloader to engage at 130 PSI cut-out and disengage at 100 PSI cut-in."),
        ("Intake Filter",
         "Cellulose/synthetic blend media rated at 10 micron filtration. Prevents airborne "
         "contaminants from entering the compression chamber and accelerating ring wear."),
        ("Discharge Line Assembly",
         "High-pressure rated steel line routing compressed air from compressor head to air dryer "
         "and wet tank. Working pressure rating: 150 PSI."),
        ("Air Dryer Interface Gasket",
         "Composite sealing gasket at the discharge line-to-air dryer connection. Prevents "
         "compressed air leakage at the system entry point to the drying circuit."),
    ])

    # Section 3 - Specifications
    pdf.add_section("3", "Specifications")
    pdf.add_body("The following specifications apply to all ACM-2800 configurations.")
    for label, value in [
        ("Displacement", "18.7 cubic inches per revolution"),
        ("Maximum Pressure", "150 PSI (governed to 130 PSI cut-out)"),
        ("Cut-in Pressure", "100 PSI +/- 3 PSI"),
        ("Cut-out Pressure", "130 PSI +/- 3 PSI"),
        ("Build-up Time (90 to 120 PSI)", "< 40 seconds at 1200 RPM"),
        ("Cooling Method", "Liquid-cooled (engine coolant circuit)"),
        ("Lubrication", "Engine oil pressure-fed"),
        ("Maximum Oil Carry-over", "28 ml per hour at rated speed"),
        ("Intake Filter Media", "Cellulose/synthetic blend, 10 micron"),
        ("Discharge Line Working Pressure", "150 PSI"),
        ("Mounting Bolt Torque", "38 ft-lbs (M12 bolts)"),
        ("Assembly Weight", "42 lbs"),
    ]:
        pdf.add_spec_row(label, value)

    # Section 4 - Installation and Removal
    pdf.add_section("4", "Installation and Removal")
    pdf.add_body(
        "Drain the air system completely before beginning compressor work. Open all drain valves "
        "on wet tank, primary tank, secondary tank, and auxiliary tanks. Disconnect discharge line, "
        "coolant hoses, oil supply line, and unloader valve air line from governor. Remove four "
        "M12 mounting bolts. During installation, apply assembly lubricant to drive gear teeth, "
        "align timing marks, and torque mounting bolts to 38 ft-lbs in a cross pattern."
    )

    # Section 5 - Theory of Operation
    pdf.add_section("5", "Theory of Operation")
    pdf.add_subsection("Compression Cycle")
    pdf.add_body(
        "The ACM-2800 is a single-cylinder reciprocating compressor driven at one-half engine "
        "crankshaft speed. During the downstroke, the piston draws ambient air through the intake "
        "filter and past the inlet reed valve. During the upstroke, air is compressed and forced "
        "past the discharge reed valve into the discharge line assembly."
    )
    pdf.add_subsection("Load/Unload Control")
    pdf.add_body(
        "The governor monitors system pressure through a sensing line connected to the wet tank. "
        "At cut-out (130 PSI), the governor signals the unloader valve to hold the inlet reed "
        "valves open, preventing pressure build. At cut-in (100 PSI), the governor releases the "
        "unloader, allowing the compressor to resume building pressure."
    )

    # Section 6 - Troubleshooting and Diagnostics
    pdf.add_section("6", "Troubleshooting and Diagnostics")

    pdf.add_subsection("6.1 Slow Air Pressure Build-up")
    pdf.add_body(
        "If build-up time from 90 to 120 PSI exceeds 40 seconds at 1,200 RPM, the most common "
        "cause is progressive wear of the piston and cylinder kit compression rings. As the "
        "rings wear, the seal between piston and cylinder wall degrades, allowing compressed air "
        "blow-by during the upstroke. This reduces effective displacement and increases build-up "
        "time. Simultaneously, the worn oil control ring allows engine oil to enter the "
        "compression chamber, resulting in elevated oil carry-over into the air system. "
        "Technicians may observe that slow build-up is accompanied by oily residue in the air "
        "dryer discharge - this combination strongly suggests piston ring wear."
    )

    pdf.add_subsection("6.2 Excessive Compressor Cycling")
    pdf.add_body(
        "If the compressor cycles between loaded and unloaded states every 30 to 90 seconds "
        "during steady highway driving with no brake usage, a system air leak is consuming air "
        "faster than the compressor can maintain pressure margin. If no external leaks are found, "
        "the governor may have an internal pressure sensing leak. A leaking governor reference "
        "chamber underestimates system pressure and commands the unloader to disengage "
        "prematurely, creating rapid load-unload cycling visible as quick oscillation between "
        "cut-in and cut-out on the dash gauge."
    )

    pdf.add_subsection("6.3 Hissing at Compressor Head")
    pdf.add_body(
        "An audible hissing from the compressor head area present only during the loaded "
        "(compression) phase indicates failure of the compressor head gasket or reed valve. "
        "If the head gasket fails, compressed air escapes between sealing surfaces during each "
        "stroke. A cracked reed valve allows backflow from the discharge line assembly into the "
        "compression chamber. Perform a leakdown test to differentiate: pressurize through the "
        "intake port - air escaping between head and cylinder body is gasket failure; air "
        "escaping through the discharge port is reed valve failure."
    )

    pdf.add_subsection("6.4 Oil Contamination in Air System")
    pdf.add_body(
        "Expelled liquid from air tank drain valves that has an oily sheen or milky appearance "
        "indicates elevated oil carry-over from the piston and cylinder kit. The excess oil "
        "contaminates the air dryer desiccant, which loses moisture-absorbing capacity and allows "
        "water vapor to pass through to the air system. The air dryer interface gasket may also "
        "show signs of oil saturation and swelling. In cold weather, accumulated moisture freezes "
        "in brake system components, potentially causing partial or complete loss of braking."
    )

    pdf.add_subsection("6.5 Unloader Valve Sluggishness")
    pdf.add_body(
        "A slow-to-engage unloader valve allows system pressure to overshoot the cut-out setting "
        "before unloading occurs. Conversely, a slow-to-disengage unloader keeps the compressor "
        "unloaded longer than necessary after pressure drops below cut-in, extending recovery "
        "time and potentially causing low-air-pressure warnings during heavy brake usage such "
        "as mountain descents. Internal friction or corrosion from moisture exposure in the "
        "unloader mechanism is the typical root cause. Replace the intake filter at recommended "
        "intervals to minimize moisture ingress that accelerates unloader corrosion."
    )

    # Section 7
    pdf.add_section("7", "Preventive Maintenance")
    pdf.add_body(
        "At each PM interval, drain all air system reservoirs and note the character of expelled "
        "liquid. At each B-service, measure compressor build-up time and record it. Replace the "
        "intake filter at the manufacturer's interval or more frequently in dusty environments. "
        "At 250,000 miles, measure oil carry-over rate by collecting air dryer discharge effluent. "
        "If rate exceeds 40 ml/hr, proactively replace the piston and cylinder kit."
    )

    filename = "PM_ACM-2800_Air_Compressor_Assembly.pdf"
    path = os.path.join(OUTPUT_DIR, filename)
    pdf.output(path)
    print(f"  {filename} ({pdf.page_no()} pages)")


# ---------------------------------------------------------------------------
# SGB-6500 Steering Gear Box
# ---------------------------------------------------------------------------
def build_steering_gearbox_manual():
    pdf = PartManualPDF("SGB-6500", "Steering Gear Box")
    pdf.alias_nb_pages()

    pdf.add_cover(
        "Steering Gear Box",
        "Service and Diagnostic Manual\nClass 8 Hydraulic Power Steering System",
        "C", "January 2025"
    )

    # Section 1
    pdf.add_section("1", "General Description")
    pdf.add_body(
        "The SGB-6500 Steering Gear Box is a hydraulic-assist recirculating ball type steering "
        "gear that provides precise directional control for Class 8 on-highway and vocational "
        "vehicles. The gear box converts rotational input from the steering column into linear "
        "thrust at the pitman arm."
    )

    # Section 2 - Components
    pdf.add_section("2", "Component Identification")
    pdf.add_body(
        "The SGB-6500 consists of seven sub-component groups described in Table 2-1."
    )
    schematic_path = os.path.join(SCHEMATIC_DIR, "Steering_Gearbox_Schematic.png")
    pdf.add_schematic(schematic_path, "Figure 2-1: SGB-6500 Steering Gear Box - Component Layout")

    pdf.add_subsection("Table 2-1: Sub-Component Identification")
    pdf.add_component_table([
        ("Input Shaft Seal",
         "Double-lip seal with dust excluder at the steering column interface. Prevents hydraulic "
         "fluid leakage externally and contaminant ingress internally."),
        ("Spool Valve",
         "Torsion bar-actuated directional control valve. Directs pressurized fluid to the "
         "appropriate side of the piston based on steering wheel input torque and direction."),
        ("Piston and Rack Assembly",
         "Hydraulic actuator converting fluid pressure into linear steering force. Contains "
         "recirculating ball mechanism for low-friction translation of rotary to linear motion."),
        ("Sector Shaft",
         "Output shaft transmitting steering torque from the piston rack to the external pitman "
         "arm through a tapered gear mesh. Factory-adjusted for zero backlash at center."),
        ("Housing Casting",
         "Ductile iron enclosure forming the hydraulic cylinder bore for the piston and mounting "
         "structure for all internal components. Rated to 2,200 PSI working pressure."),
        ("Hydraulic Fitting Set",
         "O-ring face seal fittings for pressure supply and return line connections from the "
         "power steering pump. Includes port plugs and diagnostic test port fittings."),
        ("Pitman Arm",
         "Forged steel output lever connecting the sector shaft to the vehicle steering linkage "
         "via the drag link. Splined interface with castle nut retention at 250 ft-lbs."),
    ])

    # Section 3 - Specifications
    pdf.add_section("3", "Specifications")
    pdf.add_body("The following specifications apply to all SGB-6500 configurations.")
    for label, value in [
        ("Type", "Recirculating ball, hydraulic power assist"),
        ("Ratio", "17.5:1 overall (variable)"),
        ("Maximum System Pressure", "2,200 PSI (relief valve setting)"),
        ("Normal Operating Pressure (straight ahead)", "150 - 250 PSI"),
        ("Normal Operating Pressure (full lock)", "1,600 - 1,900 PSI"),
        ("Fluid Type", "TITAN MOTORS-approved ATF or power steering fluid"),
        ("Fluid Capacity (gear box only)", "3.2 quarts"),
        ("Input Shaft Seal Type", "Double-lip with dust excluder"),
        ("Sector Shaft End-play", "0.000 - 0.002 inches (adjusted)"),
        ("Pitman Arm Nut Torque", "250 ft-lbs + cotter pin"),
        ("Housing Mounting Bolt Torque", "225 ft-lbs"),
        ("Assembly Weight", "85 lbs"),
    ]:
        pdf.add_spec_row(label, value)

    # Section 4 - Installation and Removal
    pdf.add_section("4", "Installation and Removal")
    pdf.add_body(
        "Support the front axle assembly. Disconnect the drag link from the pitman arm using a "
        "ball joint separator - do not use a pickle fork. Disconnect pressure and return "
        "hydraulic lines and cap all open lines. Disconnect the steering column intermediate "
        "shaft. Remove frame mounting bolts and lower the gear box. During installation, apply "
        "thread-locking compound to mounting bolts and torque to 225 ft-lbs. Use new O-ring "
        "seals at each hydraulic fitting. Bleed air by turning lock-to-lock several times with "
        "engine running."
    )

    # Section 5 - Theory of Operation
    pdf.add_section("5", "Theory of Operation")
    pdf.add_subsection("Hydraulic Assist Mechanism")
    pdf.add_body(
        "When the driver turns the steering wheel, the input shaft rotates a torsion bar-actuated "
        "spool valve within the gear box. The spool valve directs pressurized fluid to one side "
        "of the piston and rack assembly while returning fluid from the opposite side. The "
        "torsion bar provides proportional feedback: harder turns open the spool valve further."
    )
    pdf.add_subsection("Pressure Relief Function")
    pdf.add_body(
        "A spring-loaded poppet relief valve in the housing casting opens when system pressure "
        "exceeds 2,200 PSI, bypassing pump output to the return circuit. This protects the gear "
        "box and pump during conditions like hitting a curb or holding against a mechanical stop."
    )

    # Section 6 - Troubleshooting and Diagnostics
    pdf.add_section("6", "Troubleshooting and Diagnostics")

    pdf.add_subsection("6.1 Steering Wander at Highway Speed")
    pdf.add_body(
        "The need for constant small corrections to maintain straight-line travel is most "
        "commonly caused by excessive clearance in the sector shaft mesh with the piston and "
        "rack assembly. The gear teeth wear over high mileage, creating a dead band at center "
        "position where input shaft rotation does not produce corresponding pitman arm movement. "
        "The driver perceives this as vagueness at the straight-ahead position. Measure "
        "rotational free play at the input shaft with the drag link disconnected. Acceptable "
        "play is 2 to 4 degrees. If play exceeds 6 degrees and adjustment cannot bring it within "
        "specification, the sector shaft and piston and rack assembly are worn beyond serviceable "
        "limits."
    )

    pdf.add_subsection("6.2 Increased Steering Effort")
    pdf.add_body(
        "A gradual increase in steering effort, particularly during low-speed maneuvering, "
        "that the driver may not immediately recognize because they have adapted incrementally, "
        "can indicate that the relief valve spring in the housing casting has weakened or the "
        "poppet seat has eroded. The relief valve opens at pressures below its intended 2,200 PSI "
        "setting, silently bypassing hydraulic assist force. This symptom is easily confused with "
        "a worn power steering pump or low fluid level. Check relief valve crack pressure by "
        "monitoring system pressure at the hydraulic fitting set diagnostic port during a full-lock "
        "turn - pressure should reach 2,100 to 2,200 PSI before relief."
    )

    pdf.add_subsection("6.3 Fluid Leak at Steering Column")
    pdf.add_body(
        "Fluid seepage past a degraded input shaft seal may initially appear as barely "
        "perceptible dampness on the steering column below the floor seal, often mistaken for "
        "condensation. The seepage rate increases as the seal lip wears, eventually becoming a "
        "visible drip on the frame rail below the steering gear. Additionally, the degraded seal "
        "may allow air to be drawn into the low-pressure side of the spool valve during rapid "
        "steering input, producing a characteristic groaning or moaning sound distinct from a "
        "pump whine. If foaming is visible in the fluid reservoir after the noise occurs, air "
        "ingestion through the input shaft seal is confirmed."
    )

    pdf.add_subsection("6.4 Leak at Hydraulic Connections")
    pdf.add_body(
        "Fluid weeping at the pressure or return line connections indicates deterioration of the "
        "O-ring seals in the hydraulic fitting set. The O-rings harden over time from heat "
        "exposure and chemical interaction with power steering fluid additives. Overtorqued "
        "fittings can also deform the sealing surface. Use UV-fluorescent dye and a UV lamp to "
        "trace the exact leak origin point."
    )

    pdf.add_subsection("6.5 Pitman Arm Looseness")
    pdf.add_body(
        "Clunking noises during direction changes originating from the pitman arm area indicate "
        "that the pitman arm splined interface has developed play on the sector shaft. This "
        "occurs when the castle nut has loosened or the cotter pin has sheared, allowing the "
        "pitman arm to shift on the splines under steering load reversal. Inspect the castle nut "
        "torque and cotter pin condition. If the splines show visible fretting or wear marks, "
        "both the pitman arm and sector shaft require replacement."
    )

    # Section 7
    pdf.add_section("7", "Preventive Maintenance")
    pdf.add_body(
        "At each B-service, check fluid level and condition. Inspect input shaft seal area and "
        "all hydraulic fitting connections for weeping. At each C-service, measure steering "
        "free play at the steering wheel rim with the engine running - maximum allowable is "
        "2 inches. Check pitman arm castle nut torque and cotter pin condition. At 300,000 "
        "miles, proactively replace the input shaft seal and hydraulic fitting set O-rings."
    )

    filename = "PM_SGB-6500_Steering_Gear_Box.pdf"
    path = os.path.join(OUTPUT_DIR, filename)
    pdf.output(path)
    print(f"  {filename} ({pdf.page_no()} pages)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Generating TITAN MOTORS Part Manuals...")
    build_turbocharger_manual()
    build_tcm_manual()
    build_exhaust_manifold_manual()
    build_air_compressor_manual()
    build_steering_gearbox_manual()
    print("Done.")
