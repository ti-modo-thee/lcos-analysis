#!/usr/bin/env python3
"""
LCOS Analysis - Generate CSV files for Flourish heatmap visualization.

This script calculates the Levelized Cost of Storage (LCOS) for various
energy storage technologies across a grid of discharge durations and
cycling frequencies, then outputs CSV files suitable for Flourish.

Two versions are generated:
- With Pumped hydro (all technologies)
- Without Pumped hydro (excludes this technology)

Author: Based on methodology from LCOS Analysis handover document
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List

# =============================================================================
# TECHNOLOGY PARAMETERS
# =============================================================================

base_technologies = {
    "Li-ion": {
        "capex_power": 250,      # $/kW
        "capex_energy": 120,     # $/kWh
        "efficiency": 0.85,      # Round-trip efficiency
        "lifetime_years": 15,    # Calendar life (years)
        "cycle_life": 6000,      # Total cycles supported
        "fixed_om_frac": 0.02,   # 2% of CAPEX/year
        "var_om": 1.0,           # $/MWh
    },
    "Pumped hydro": {
        # Thunder Said Energy typical: $2,250/kW
        # NREL ATB 2024 range: $1,999-5,505/kW
        # PNNL Gordon Butte: $2,710/kW direct
        # Source: https://thundersaidenergy.com/downloads/pumped-hydro-the-economics/
        "capex_power": 2250,       # Thunder Said Energy typical (range: $2,000-5,500/kW)
        "capex_energy": 50,        # Reservoir costs relatively stable
        "efficiency": 0.80,
        "lifetime_years": 60,
        "cycle_life": 50000,
        "fixed_om_frac": 0.02,
        "var_om": 0.8,
    },
    "CAES": {
        # Hydrostor A-CAES (Willow Rock project: 500MW/4GWh @ $1.5B = $3,000/kW for 8h)
        # CEO quote (July 2024): "$3,000/kW for 10h system, ~$50/kWh per additional hour"
        # Reverse-engineered: capex_power = $2,500/kW, capex_energy = $50/kWh
        # Note: Corre Energy (salt cavern CAES) filed for bankruptcy - Hydrostor is main player
        "capex_power": 2500,       # Hydrostor A-CAES (purpose-built caverns)
        "capex_energy": 50,        # Hydrostor marginal cost per hour
        "efficiency": 0.60,        # A-CAES with thermal storage (adiabatic)
        "lifetime_years": 50,
        "cycle_life": 15000,
        "fixed_om_frac": 0.02,
        "var_om": 1.0,
    },
    "LAES": {
        # Energy Dome CO2 Battery weighted with LDES Council benchmarking data
        # LDES Council 2025 range: $158-471/kWh at 10h (Intraday Compressed Gas)
        # Target: $170/kWh at 10h → $900 + $80×10 = $1,700/kW
        # Higher power cost = more competitive at longer durations
        "capex_power": 900,        # Weighted with LDES Council (vs Energy Dome $700)
        "capex_energy": 80,        # Energy Dome CO2 Battery dome/storage
        "efficiency": 0.65,        # Energy Dome data (LDES Council range: 53-72%)
        "lifetime_years": 30,
        "cycle_life": 10000,
        "fixed_om_frac": 0.02,
        "var_om": 1.0,
    },
    "Iron-air": {
        "capex_power": 1700,       # Form Energy data
        "capex_energy": 5,         # Form Energy data
        "efficiency": 0.40,        # Form Energy data
        "lifetime_years": 17,      # Form Energy data
        "cycle_life": 10000,       # Form Energy data
        "fixed_om_frac": 0.02,
        "var_om": 1.0,
    },
    "VRFB": {
        # PNNL methodology: stack (power) ~$350/kW + BOP, electrolyte (energy) ~$178/kWh
        # Source: https://www.pnnl.gov/sites/default/files/media/file/RedoxFlow_Methodology.pdf
        # Adjusted to reflect VRFB advantage: LOW energy cost relative to power cost
        # Validates at 10h: $1,000 + $180×10 = $2,800/kW → $280/kWh (within LDES Council range)
        "capex_power": 1000,       # Stack + BOP + power electronics
        "capex_energy": 180,       # Electrolyte tanks (scales with duration)
        "efficiency": 0.75,
        "lifetime_years": 25,      # LDES Council: 20-25 years
        "cycle_life": 20000,
        "fixed_om_frac": 0.02,
        "var_om": 1.0,
    },
}

# =============================================================================
# ANALYSIS PARAMETERS
# =============================================================================

DISCOUNT_RATE = 0.08  # 8% discount rate
HOURS_PER_YEAR = 8760
HOURS_PER_CYCLE_MAX = HOURS_PER_YEAR / 2  # 4380h (accounts for charge + discharge)

# Grid parameters
NUM_POINTS = 45
DURATION_MIN = 1      # hours
DURATION_MAX = 702    # hours
FREQUENCY_MIN = 1     # cycles/year
FREQUENCY_MAX = 1600  # cycles/year


# =============================================================================
# LCOS CALCULATION FUNCTIONS
# =============================================================================

def calculate_crf(rate: float, years: float) -> float:
    """
    Calculate the Capital Recovery Factor (CRF).

    CRF converts a present value into an annualized payment over n years.
    Formula: CRF = r * (1+r)^n / ((1+r)^n - 1)
    """
    if years <= 0:
        return float('inf')
    if rate == 0:
        return 1 / years
    factor = (1 + rate) ** years
    return rate * factor / (factor - 1)


def calculate_lcos(
    duration: float,
    frequency: float,
    capex_power: float,
    capex_energy: float,
    efficiency: float,
    lifetime_years: float,
    cycle_life: float,
    fixed_om_frac: float,
    var_om: float,
    discount_rate: float = DISCOUNT_RATE
) -> float:
    """
    Calculate LCOS (Levelized Cost of Storage) in $/MWh.

    LCOS = (Annualized CAPEX + Annual Fixed O&M) / Energy Delivered per Year + Variable O&M
    """
    # 1. Total CAPEX ($/kW)
    capex_total = capex_power + capex_energy * duration

    # 2. Effective lifetime (limited by calendar life or cycle life)
    cycle_limited_life = cycle_life / frequency if frequency > 0 else float('inf')
    effective_lifetime = min(lifetime_years, cycle_limited_life)

    # 3. Capital Recovery Factor
    crf = calculate_crf(discount_rate, effective_lifetime)

    # 4. Annualized CAPEX ($/kW/year)
    annualized_capex = capex_total * crf

    # 5. Annual Fixed O&M ($/kW/year)
    annual_fixed_om = capex_total * fixed_om_frac

    # 6. Energy delivered per year (MWh/kW/year)
    # = Duration (h) × Frequency (cycles/year) × Efficiency / 1000 (kWh→MWh)
    energy_per_year = duration * frequency * efficiency / 1000

    if energy_per_year <= 0:
        return float('inf')

    # 7. LCOS ($/MWh)
    lcos = (annualized_capex + annual_fixed_om) / energy_per_year + var_om

    return lcos


def create_category(best_tech: str, gap: float) -> str:
    """
    Create category string based on best technology and gap to second best.

    Gap thresholds:
    - < 1%: "on par"
    - 1-5%: "{tech} < 5%"
    - 5-10%: "{tech} 5%"
    - 10-20%: "{tech} 10%"
    - 20-30%: "{tech} 20%"
    - 30-40%: "{tech} 30%"
    - >= 40%: "{tech} 40%+"
    """
    if gap < 0.01:
        return "on par"
    elif gap < 0.05:
        return f"{best_tech} < 5%"
    elif gap < 0.10:
        return f"{best_tech} 5%"
    elif gap < 0.20:
        return f"{best_tech} 10%"
    elif gap < 0.30:
        return f"{best_tech} 20%"
    elif gap < 0.40:
        return f"{best_tech} 30%"
    else:
        return f"{best_tech} 40%+"


def format_value(value: float) -> str:
    """Format numeric value: integers without .0, others with 2 decimals."""
    if value >= 1:
        rounded = round(value)
        return str(rounded)
    else:
        return f"{value:.2f}"


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def generate_lcos_csv(
    technologies: Dict,
    output_filename: str,
    durations: np.ndarray,
    frequencies: np.ndarray
) -> pd.DataFrame:
    """
    Generate LCOS analysis and save to CSV for Flourish.

    Returns DataFrame with columns: Duration, Frequency, Category
    """
    results = {}  # Use dict to avoid duplicates after rounding

    for duration in durations:
        for frequency in frequencies:
            # Check physical constraint: 2 × Duration × Frequency ≤ 8760
            # Equivalent to: Duration × Frequency ≤ 4380
            if duration * frequency > HOURS_PER_CYCLE_MAX:
                continue

            # Format values for CSV (do this early to check for duplicates)
            duration_fmt = format_value(duration)
            frequency_fmt = format_value(frequency)
            key = (duration_fmt, frequency_fmt)

            # Skip if we already have this (Duration, Frequency) pair
            if key in results:
                continue

            # Verify constraint after rounding
            d_check = float(duration_fmt)
            f_check = float(frequency_fmt)
            if d_check * f_check > HOURS_PER_CYCLE_MAX:
                continue

            # Calculate LCOS for each technology
            lcos_values = {}
            for tech_name, params in technologies.items():
                lcos = calculate_lcos(
                    duration=duration,
                    frequency=frequency,
                    **params
                )
                lcos_values[tech_name] = lcos

            # Sort by LCOS (ascending)
            sorted_techs = sorted(lcos_values.items(), key=lambda x: x[1])

            if len(sorted_techs) < 2:
                continue

            best_tech, best_lcos = sorted_techs[0]
            second_tech, second_lcos = sorted_techs[1]

            # Calculate gap
            if best_lcos > 0:
                gap = (second_lcos - best_lcos) / best_lcos
            else:
                gap = 0

            # Create category
            category = create_category(best_tech, gap)

            results[key] = {
                "Duration": duration_fmt,
                "Frequency": frequency_fmt,
                "Category": category
            }

    # Create DataFrame and save
    df = pd.DataFrame(list(results.values()))
    df.to_csv(output_filename, index=False)

    return df


def print_summary(df: pd.DataFrame, title: str):
    """Print summary statistics for a results DataFrame."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")
    print(f"Total points: {len(df)}")

    # Count by technology (extract first word from Category)
    tech_counts = df["Category"].str.split().str[0].value_counts()
    print("\nTechnologies distribution:")
    for tech, count in tech_counts.items():
        pct = 100 * count / len(df)
        print(f"  {tech}: {count} points ({pct:.1f}%)")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def generate_combined_csv(
    durations: np.ndarray,
    frequencies: np.ndarray,
    output_filename: str = "LDES_LCOS_flourish_combined.csv"
) -> pd.DataFrame:
    """
    Generate a combined CSV with both PHES included and excluded versions.

    The output has columns matching the Flourish visualization:
    - Discharge duration (h)
    - Cycles per year
    - Category
    - Filter (PHES excluded / PHES included)
    """
    all_results = []

    # Technologies without Pumped hydro (PHES excluded)
    techs_sans_pumped = {k: v for k, v in base_technologies.items() if k != "Pumped hydro"}

    for filter_name, technologies in [
        ("PHES excluded", techs_sans_pumped),
        ("PHES included", base_technologies)
    ]:
        seen_keys = set()

        for duration in durations:
            for frequency in frequencies:
                # Check physical constraint
                if duration * frequency > HOURS_PER_CYCLE_MAX:
                    continue

                # Format values
                duration_fmt = format_value(duration)
                frequency_fmt = format_value(frequency)
                key = (duration_fmt, frequency_fmt, filter_name)

                if key in seen_keys:
                    continue
                seen_keys.add(key)

                # Verify constraint after rounding
                d_check = float(duration_fmt)
                f_check = float(frequency_fmt)
                if d_check * f_check > HOURS_PER_CYCLE_MAX:
                    continue

                # Calculate LCOS for each technology
                lcos_values = {}
                for tech_name, params in technologies.items():
                    lcos = calculate_lcos(
                        duration=duration,
                        frequency=frequency,
                        **params
                    )
                    lcos_values[tech_name] = lcos

                # Sort by LCOS (ascending)
                sorted_techs = sorted(lcos_values.items(), key=lambda x: x[1])

                if len(sorted_techs) < 2:
                    continue

                best_tech, best_lcos = sorted_techs[0]
                second_tech, second_lcos = sorted_techs[1]

                # Calculate gap
                gap = (second_lcos - best_lcos) / best_lcos if best_lcos > 0 else 0

                # Create category
                category = create_category(best_tech, gap)

                all_results.append({
                    "Discharge duration (h)": duration_fmt,
                    "Cycles per year": frequency_fmt,
                    "Category": category,
                    "Filter": filter_name
                })

    # Create DataFrame and save
    df = pd.DataFrame(all_results)
    df.to_csv(output_filename, index=False)

    return df


def main():
    """Generate CSV files for Flourish."""

    # Create analysis grids (logarithmic scales)
    durations = np.logspace(
        np.log2(DURATION_MIN),
        np.log2(DURATION_MAX),
        num=NUM_POINTS,
        base=2
    )

    frequencies = np.logspace(
        0,  # log10(1) = 0
        np.log10(FREQUENCY_MAX),
        num=NUM_POINTS
    )

    print("LCOS Analysis - Generating Flourish CSV files")
    print(f"Duration range: {DURATION_MIN}h to {DURATION_MAX}h ({NUM_POINTS} points, log2 scale)")
    print(f"Frequency range: {FREQUENCY_MIN} to {FREQUENCY_MAX} cycles/year ({NUM_POINTS} points, log10 scale)")
    print(f"Physical constraint: Duration × Frequency ≤ {HOURS_PER_CYCLE_MAX}h")

    # Generate COMBINED CSV for Flourish (with Filter column for toggle)
    print("\n[1/3] Generating COMBINED version for Flourish...")
    df_combined = generate_combined_csv(
        durations=durations,
        frequencies=frequencies,
        output_filename="LDES_LCOS_flourish_combined.csv"
    )
    print(f"\n{'='*60}")
    print(" COMBINED VERSION (for Flourish toggle)")
    print(f"{'='*60}")
    print(f"Total points: {len(df_combined)}")
    print(f"  - PHES excluded: {len(df_combined[df_combined['Filter'] == 'PHES excluded'])} points")
    print(f"  - PHES included: {len(df_combined[df_combined['Filter'] == 'PHES included'])} points")

    # Version 1: WITH Pumped hydro (all technologies)
    print("\n[2/3] Generating version WITH Pumped hydro...")
    df_with_pumped = generate_lcos_csv(
        technologies=base_technologies,
        output_filename="LDES_LCOS_flourish_AVEC_Pumped_hydro.csv",
        durations=durations,
        frequencies=frequencies
    )
    print_summary(df_with_pumped, "VERSION AVEC Pumped hydro")

    # Version 2: WITHOUT Pumped hydro
    print("\n[3/3] Generating version WITHOUT Pumped hydro...")
    techs_sans_pumped = {k: v for k, v in base_technologies.items() if k != "Pumped hydro"}
    df_sans_pumped = generate_lcos_csv(
        technologies=techs_sans_pumped,
        output_filename="LDES_LCOS_flourish_SANS_Pumped_hydro.csv",
        durations=durations,
        frequencies=frequencies
    )
    print_summary(df_sans_pumped, "VERSION SANS Pumped hydro")

    print("\n" + "="*60)
    print(" FILES GENERATED:")
    print("="*60)
    print("  - LDES_LCOS_flourish_combined.csv  <-- USE THIS FOR FLOURISH")
    print("  - LDES_LCOS_flourish_AVEC_Pumped_hydro.csv")
    print("  - LDES_LCOS_flourish_SANS_Pumped_hydro.csv")
    print("\nReady for Flourish import!")


if __name__ == "__main__":
    main()


# =============================================================================
# ASSUMPTIONS TABLE - DOCUMENTATION
# =============================================================================
#
# All values in USD
#
# | Technology    | capex_power | capex_energy | RTE   | Life | Cycles | Fixed O&M | Var O&M |
# |               | ($/kW)      | ($/kWh)      |       | (yr) |        | (frac)    | ($/MWh) |
# |---------------|-------------|--------------|-------|------|--------|-----------|---------|
# | Li-ion 2025   | 250         | 120          | 0.85  | 15   | 6000   | 0.02      | 1.0     |
# | Pumped hydro  | 2250        | 50           | 0.80  | 60   | 50000  | 0.02      | 0.8     |
# | CAES          | 2500        | 50           | 0.60  | 50   | 15000  | 0.02      | 1.0     |
# | LAES/CO2      | 900         | 80           | 0.65  | 30   | 10000  | 0.02      | 1.0     |
# | Iron-air      | 1700        | 5            | 0.40  | 17   | 10000  | 0.02      | 1.0     |
# | VRFB          | 1000        | 180          | 0.75  | 25   | 20000  | 0.02      | 1.0     |
# | Hydrogen*     | 3000        | 20           | 0.38  | 20   | 15000  | 0.03      | 1.0     |
#
# * Hydrogen not yet included in model
#
# =============================================================================
# SOURCES & REFERENCES
# =============================================================================
#
# Li-ion:
#   - Modo Energy internal cost study (proprietary)
#
# Pumped hydro:
#   - Thunder Said Energy: https://thundersaidenergy.com/downloads/Global-Pumped-Hydro-Projects.xlsx
#   - NREL ATB 2024: https://atb.nrel.gov/electricity/2024/pumped-storage-hydropower
#
# CAES (Hydrostor A-CAES):
#   - Willow Rock project: https://hydrostor.ca/projects/willow-rock-energy-storage-center/
#   - DOE Loan: https://www.energy.gov/lpo/hydrostor
#   - CEO quote (July 2024): "$3,000/kW for 10h, ~$50/kWh marginal"
#     Source: https://www.utilitydive.com/news/hydrostor-caes-long-duration-energy-storage-california-willow-rock/721444/
#   - Note: Corre Energy (salt cavern CAES) filed for bankruptcy in 2024
#
# LAES / CO2 Battery:
#   - Energy Dome (technology provider) - data shared directly
#   - Company website: https://energydome.com/
#
# Iron-air:
#   - Form Energy (technology provider) - data shared directly
#   - Company website: https://formenergy.com/
#
# VRFB:
#   - BloombergNEF LDES Survey 2024: https://about.bnef.com/blog/lithium-ion-batteries-are-set-to-face-competition-from-novel-tech-for-long-duration-storage-bloombergnef-research/
#   - PV Magazine analysis: https://www.pv-magazine.com/2024/03/15/evaluating-profitability-of-vanadium-flow-batteries/
#   - Note: Survey shows $423/kWh (China) to $701/kWh (RoW) - our values are optimistic
#
# Hydrogen (not yet in model):
#   - DOE LDES Report: https://www.energy.gov/sites/default/files/2024-08/Achieving%20the%20Promise%20of%20Low-Cost%20Long%20Duration%20Energy%20Storage_FINAL_08052024.pdf
#   - PNNL methodology: https://www.pnnl.gov/sites/default/files/media/file/Hydrogen_Methodology.pdf
#   - Capex = Electrolyzer (~$1,200/kW) + Fuel Cell (~$1,800/kW)
#   - RTE = ~70% electrolysis × ~55% fuel cell ≈ 38%
#
# General references:
#   - LDES Council 2024 Report: https://ldescouncil.com/2024-ldes-annual-report/
#   - Lazard LCOE+ 2024: https://www.lazard.com/media/xemfey0k/lazards-lcoeplus-june-2024-_vf.pdf
#
# =============================================================================
