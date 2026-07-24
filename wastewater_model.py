
#Wastewater Treatment & Reuse System Model 
#Based on real 2025 data from the Guelph Water Resource Recovery Centre

import math
import matplotlib.pyplot as plt

# inout data 
influent = {
    "flow_m3_per_day": 52783,      # 2025 whole plant average 
    "BOD": 287,                    # biochemical oxygen demand mg/L
    "TSS": 262,                    # total suspended solids mg/L
    "TP": 5.30,                    # total phosphorus mg/L
    "TN": 32.2,                    # nitrogen mg/L
    "E_coli": 1.0e7,               # Colony forming units/100mL
}

# REAL aeration tank volumes from Guelph's Wastewater Treatment and Biosolids from City of Guelph / Jacobs
#   Plant 1: 4,347 m3   Plant 2: 4,983 m3
#   Plant 3: 4,076 m3   Plant 4: 12,871 m3
# This is the actual as-built design volume, not an assumption.
AERATION_VOLUME_M3 = 4347 + 4983 + 4076 + 12871  

reuse_standard = {
    "BOD": 10,
    "TSS": 10,
    "TP": 1,
    "TN": 10,
    "E_coli": 200,
}

# Kinetic constants + design parameters
kinetics = {
    "Y": 0.6,           # yield coefficient (g biomass / g BOD)
    "k": 5.0,           # max substrate utilization rate (1/day)
    "Ks": 60,           # half-velocity constant (mg/L)
    "kd": 0.06,         # endogenous decay rate (1/day)
    "theta_c": 8,       # sludge age / Solids Retention Time (days)
    "f": 0.68,          # BOD5 to ultimate BOD conversion factor
    "MLSS": 3000,       # Mixed Liquor Suspended Solids (mg/L)
}

# helper functions
def remove_percent(value, percent_removed):
    # Remove a percentage of a pollutant 
    return value * (1 - percent_removed)

def mass_balance_kg_per_day(concentration_mg_per_L, flow_m3_per_day):
    # Convert concentration (mg/L) to mass loading (kg/day) 
    return concentration_mg_per_L * flow_m3_per_day / 1000

# treatment stages
def preliminary_treatment(water):
    #Screening + grit removal 
    water["TSS"] = remove_percent(water["TSS"], 0.10)
    return water

def primary_treatment(water, flow_m3_per_day):
    #Primary clarifier with sludge tracking 
    TSS_before = water["TSS"]
    water["BOD"] = remove_percent(water["BOD"], 0.30)
    water["TSS"] = remove_percent(water["TSS"], 0.55)
    water["TP"] = remove_percent(water["TP"], 0.10)
    water["_primary_sludge_kg_day"] = mass_balance_kg_per_day(TSS_before - water["TSS"], flow_m3_per_day)
    return water

def secondary_treatment(water, flow_m3_per_day, k_const):
    # Activated sludge process using Monod kinetics (CSTR) 
    Y = k_const["Y"]
    k = k_const["k"]
    Ks = k_const["Ks"]
    kd = k_const["kd"]
    theta_c = k_const["theta_c"]
    f = k_const["f"]
    MLSS = k_const["MLSS"]

    S0 = water["BOD"]

    # Monod equation for effluent BOD (soluble substrate)
    S = Ks * (1 + kd * theta_c) / (theta_c * (Y * k - kd) - 1)
    water["BOD"] = max(S, 0)

    BOD_removed_kg = mass_balance_kg_per_day(S0 - water["BOD"], flow_m3_per_day)
    Px_kg = (Y * BOD_removed_kg) / (1 + kd * theta_c)          # biomass production
    Ro_kg = (BOD_removed_kg / f) - 1.42 * Px_kg               # oxygen requirement

    # Food to Microorganism ratio
    # V comes from the real design HRT (see AERATION_VOLUME_M3) 
    FM_ratio = (flow_m3_per_day * S0) / (AERATION_VOLUME_M3 * MLSS)

    # Simple percentage removals (can be replaced later with more equations)
    water["TSS"] = remove_percent(water["TSS"], 0.85)
    water["TN"] = remove_percent(water["TN"], 0.30)
    water["TP"] = remove_percent(water["TP"], 0.20)

    return water, Px_kg, Ro_kg, FM_ratio

def tertiary_treatment(water):
    # Tertiary treatment (filtration + nutrient polishing) 
    water["TSS"] = remove_percent(water["TSS"], 0.60)
    water["TN"] = remove_percent(water["TN"], 0.70)
    water["TP"] = remove_percent(water["TP"], 0.85)
    return water

def disinfection(water, tank_volume_m3, flow_m3_per_day, decay_rate_per_min=0.35):
    """First-order disinfection.
    decay_rate_per_min: NOT plant-specific (no published Guelph value found).
    Set to 0.25/min based on literature ranges for first-order pathogen
    inactivation (~0.17-0.5/min), which is far more defensible than the
    previous 1.0/min guess -- but still an assumption, not a measured
    Guelph design parameter. Worth flagging as a limitation.
    """
    retention_time_days = tank_volume_m3 / flow_m3_per_day
    retention_time_minutes = retention_time_days * 24 * 60
    N0 = water["E_coli"]
    water["E_coli"] = N0 * math.exp(-decay_rate_per_min * retention_time_minutes)
    return water, retention_time_minutes

def henry_law_oxygen_saturation():
    # Henry's Law for oxygen saturation at 20C 
    P_O2_atm = 0.21
    k_H = 769.23
    O2_molar_mass_mg = 32000
    C_mol = P_O2_atm / k_H
    return C_mol * O2_molar_mass_mg

# main simulation
def run_treatment_train(influent, kinetics):
    flow = influent["flow_m3_per_day"]
    water = influent.copy()
    water["flow_m3_per_day"] = flow

    history = {"Influent": water.copy()}

    water = preliminary_treatment(water)
    history["After Preliminary"] = water.copy()

    water = primary_treatment(water, flow)
    history["After Primary"] = water.copy()

    water, sludge_produced, oxygen_required, FM_ratio = secondary_treatment(water, flow, kinetics)
    history["After Secondary"] = water.copy()

    aeration_volume_m3 = AERATION_VOLUME_M3
    HRT_days = aeration_volume_m3 / flow

    water = tertiary_treatment(water)
    history["After Tertiary"] = water.copy()

    TP_removed = history["After Secondary"]["TP"] - water["TP"]
    chem_sludge = mass_balance_kg_per_day(TP_removed, flow) * 3.0

    # Contact tank volume estimated from the plant's real stated performance:
    # "contact time at ADF [64,000 m3/day] is slightly less than the MOE
    # guideline of 30 minutes" (Guelph WWTP Master Plan, Sec 6.7). Backing out
    # a volume from 30 min at 64,000 m3/day gives 1,333 m3; using 1,300 m3
    # here to be "slightly less than" the guideline.
    RATED_CAPACITY_M3_PER_DAY = 64000
    contact_tank_volume_m3 = 1300  # m3, design-basis estimate (see note above)
    water, contact_time_min = disinfection(water, contact_tank_volume_m3, flow)
    history["After Disinfection"] = water.copy()

    extra_results = {
        "sludge_produced_kg_per_day": sludge_produced,
        "oxygen_required_kg_per_day": oxygen_required,
        "FM_ratio": FM_ratio,
        "HRT_days": HRT_days,
        "MLSS": kinetics["MLSS"],
        "chlorine_contact_time_min": contact_time_min,
        "oxygen_saturation_mg_per_L": henry_law_oxygen_saturation(),
        "primary_sludge_kg_day": water.get("_primary_sludge_kg_day", 0),
        "chem_sludge_kg_day": chem_sludge,
        "blower_power_estimate": oxygen_required / 0.75,
    }

    return water, history, extra_results

# REPORT 
def print_report(history, standard, extra_results, flow):

    print("\nWASTEWATER TREATMENT REPORT")

    print("\nConcentrations at each stage:")
    for stage in history:
        values = history[stage]
        print(stage)
        print("  BOD:", values["BOD"], "mg/L")
        print("  TSS:", values["TSS"], "mg/L")
        print("  TP :", values["TP"], "mg/L")
        print("  TN :", values["TN"], "mg/L")
        print("  E.coli:", values["E_coli"])
        print()

    print("Design Parameters")
    print("HRT:", round(extra_results["HRT_days"], 2), "days")
    print("F/M Ratio:", round(extra_results["FM_ratio"], 3))
    print("MLSS:", extra_results["MLSS"], "mg/L")
    print("Oxygen Required:", round(extra_results["oxygen_required_kg_per_day"], 1), "kg/day")
    print("Oxygen supply needed (accounting for transfer efficiency):", round(extra_results["blower_power_estimate"], 1), "kg/day")

    print("\nSludge Production")
    primary = extra_results.get("primary_sludge_kg_day", 0)
    biological = extra_results["sludge_produced_kg_per_day"]
    chemical = extra_results.get("chem_sludge_kg_day", 0)
    total = primary + biological + chemical

    print("Primary:", primary, "kg/day")
    print("Biological:", biological, "kg/day")
    print("Chemical:", chemical, "kg/day")
    print("Total:", total, "kg/day")

    print("\nFinal Effluent Check")
    final = history["After Disinfection"]

    for pollutant in standard:
        if final[pollutant] <= standard[pollutant]:
            print(pollutant, ": PASS")
        else:
            print(pollutant, ": FAIL")

    print("\nRemoval Efficiencies")
    influent = history["Influent"]

    for pollutant in ["BOD", "TSS", "TN", "TP"]:
        removal = ((influent[pollutant] - final[pollutant]) / influent[pollutant]) * 100
        print(pollutant, "Removal:", round(removal, 1), "%")
#GRAPHS 
def generate_graphs(history, extra_results, save_path_prefix="chart"):
    """
    Builds the two report charts straight from the model's own output:
      1. Pollutant concentration through each treatment stage
      2. Sludge production breakdown by source
    Saves them as PNG files next to the script and shows them.
    """
    stages = list(history.keys())
    bod = [history[s]["BOD"] for s in stages]
    tss = [history[s]["TSS"] for s in stages]
    tp  = [history[s]["TP"] for s in stages]
    tn  = [history[s]["TN"] for s in stages]

    # --- Chart 1: Pollutant concentration vs treatment stage ---
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(stages, bod, marker="o", linewidth=2, label="BOD (mg/L)")
    ax.plot(stages, tss, marker="o", linewidth=2, label="TSS (mg/L)")
    ax.plot(stages, tn, marker="o", linewidth=2, label="TN (mg/L)")
    ax.plot(stages, tp, marker="o", linewidth=2, label="TP (mg/L)")

    ax.set_title("Pollutant Concentration Through the Treatment Train\n(Guelph WRRC 2025 influent data)",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("Concentration (mg/L)")
    ax.set_xlabel("Treatment Stage")
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    fig.tight_layout()
    fig.savefig(f"{save_path_prefix}_treatment_train.png", dpi=200)

    # --- Chart 2: Sludge production breakdown ---
    sludge_sources = ["Primary\n(clarifier)", "Biological\n(secondary)", "Chemical\n(P removal)"]
    sludge_values = [
        extra_results["primary_sludge_kg_day"],
        extra_results["sludge_produced_kg_per_day"],
        extra_results["chem_sludge_kg_day"],
    ]
    total = sum(sludge_values)

    fig2, ax2 = plt.subplots(figsize=(7, 5.5))
    bars = ax2.bar(sludge_sources, sludge_values, color=["#4C72B0", "#55A868", "#C44E52"])
    for b, v in zip(bars, sludge_values):
        ax2.text(b.get_x() + b.get_width() / 2, v + total * 0.015, f"{v:,.0f} kg/day",
                  ha="center", fontsize=10, fontweight="bold")

    ax2.axhline(total, color="black", linestyle="--", linewidth=1)
    ax2.text(2.5, total * 1.02, f"Total: {total:,.0f} kg/day", ha="right", fontsize=10, style="italic")

    ax2.set_title("Simulated Daily Sludge Production by Source", fontsize=13, fontweight="bold")
    ax2.set_ylabel("kg/day")
    ax2.grid(True, axis="y", alpha=0.3)
    fig2.tight_layout()
    fig2.savefig(f"{save_path_prefix}_sludge_breakdown.png", dpi=200)

    print(f"\nSaved graphs: {save_path_prefix}_treatment_train.png, {save_path_prefix}_sludge_breakdown.png")
    plt.show()

if __name__ == "__main__":
    final_water, history, extra = run_treatment_train(influent, kinetics)
    print_report(history, reuse_standard, extra, influent["flow_m3_per_day"])
    generate_graphs(history, extra)