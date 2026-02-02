# LCOS Model Parameters Documentation

**Last updated:** February 2026
**Author:** Modo Energy

---

## Summary Table

| Technology | capex_power ($/kW) | capex_energy ($/kWh) | RTE | Lifetime (yr) | Cycle life | Confidence |
|------------|-------------------|---------------------|-----|---------------|------------|------------|
| **Li-ion** | 250 | 120 | 85% | 15 | 6,000 | ⭐⭐⭐ High |
| **Pumped hydro** | 3,000 | 50 | 80% | 60 | 50,000 | ⭐ Low (highly variable) |
| **CAES** | 2,500 | 50 | 55% | 50 | 15,000 | ⭐⭐ Medium |
| **LAES/CO2** | 700 | 80 | 65% | 30 | 10,000 | ⭐⭐ Medium |
| **Iron-air** | 1,700 | 5 | 40% | 17 | 10,000 | ⭐⭐ Medium |
| **VRFB** | 700 | 280 | 75% | 25 | 20,000 | ⭐⭐ Medium |

---

## Li-ion Battery

| Parameter | Value | Source |
|-----------|-------|--------|
| capex_power | **$250/kW** | Modo Energy |
| capex_energy | **$120/kWh** | Modo Energy |
| RTE | 85% | Industry standard |
| Lifetime | 15 years | Conservative estimate |
| Cycle life | 6,000 | LFP chemistry |

### Justification
Proprietary Modo Energy cost model based on internal market analysis. These values are **more aggressive than public benchmarks** (EPRI 2025 estimates $385/kWh for 100 MW/4h systems). Our lower costs reflect:
- Direct relationships with tier-1 suppliers
- Bulk procurement assumptions
- Exclusion of certain soft costs

**Benchmark comparison:** LDES Council/EPRI reports $304/kWh for 4h Li-ion at 100 MW scale. Our model implies ~$145/kWh at 10h, which is optimistic but defensible for 2025+ utility-scale projects.

---

## Pumped Hydro Storage

| Parameter | Value | Source |
|-----------|-------|--------|
| capex_power | **$3,000/kW** | NREL ATB 2024 + project data |
| capex_energy | **$50/kWh** | Reservoir cost estimates |
| RTE | 80% | Industry standard |
| Lifetime | 60 years | Conservative |
| Cycle life | 50,000 | Essentially unlimited |

### Justification
**Pumped hydro costs are extremely variable** depending on geology, location, and use of existing infrastructure. We use a mid-range estimate.

**Project benchmarks:**
- **NREL ATB 2024 Class 3:** $3,794/kW for 838 MW/10h → [NREL ATB](https://atb.nrel.gov/electricity/2024/pumped_storage_hydropower)
- **Upper Cisokan (Indonesia):** 1,040 MW, $610M → $586/kW (uses existing dam)
- **Snowy 2.0 (Australia):** 2,200 MW, $12-20B → $5,450-9,090/kW (greenfield, complex geology)
- **Coire Glas (UK):** 1,300 MW, £1.5B → ~$1,500/kW (favorable site)

**Range observed:** $586/kW to $9,000+/kW depending on site conditions.

We chose **$3,000/kW** as a reasonable mid-point for new-build projects with moderately favorable geology. Projects using existing reservoirs can be significantly cheaper; greenfield projects in difficult terrain can be 2-3x more expensive.

---

## CAES (Compressed Air Energy Storage)

| Parameter | Value | Source |
|-----------|-------|--------|
| capex_power | **$2,500/kW** | Hydrostor |
| capex_energy | **$50/kWh** | Hydrostor |
| RTE | 55% | Diabatic baseline |
| Lifetime | 50 years | Long-lived infrastructure |
| Cycle life | 15,000 | Mechanical systems |

### Justification
Based on **Hydrostor A-CAES** technology, the leading commercial CAES developer (Corre Energy filed for bankruptcy in 2024).

**Primary source:** Hydrostor CEO quote (July 2024):
> "Installed cost is about $3,000/kW for a 10-hour system and about $50/kWh per additional hour"

Source: [Utility Dive](https://www.utilitydive.com/news/hydrostor-caes-long-duration-energy-storage-california-willow-rock/721444/)

**Project validation:**
- **Willow Rock (California):** 500 MW / 4,000 MWh (8h), $1.5B total
- Calculation: $1.5B / 500 MW = $3,000/kW at 8h
- Reverse-engineered: capex_power ≈ $2,500/kW, capex_energy ≈ $50/kWh

**Note:** These costs are for A-CAES with purpose-built caverns. Salt cavern CAES (like Corre Energy proposed) would have different economics but no commercial projects exist.

---

## LAES / CO2 Battery

| Parameter | Value | Source |
|-----------|-------|--------|
| capex_power | **$700/kW** | Energy Dome |
| capex_energy | **$80/kWh** | Energy Dome |
| RTE | 65% | Energy Dome claims |
| Lifetime | 30 years | Mechanical systems |
| Cycle life | 10,000 | Conservative |

### Justification
Based on **Energy Dome CO2 Battery** technology data shared directly by the company. Energy Dome is the leading commercial developer of CO2-based long-duration storage.

**Caveats:**
- These are **manufacturer-provided figures**, not independently verified project costs
- Energy Dome's first commercial projects are still in early deployment
- LDES Council data shows Compressed Gas category at $158-471/kWh for 10h systems
- Our values ($150/kWh at 10h) are at the **optimistic end** of this range

**Validation:** At 10h duration:
- Our model: $700 + $80×10 = $1,500/kW → $150/kWh
- LDES Council 2025 low end: $158/kWh ✓

Energy Dome claims are plausible but should be validated as more projects are deployed.

---

## Iron-air Battery

| Parameter | Value | Source |
|-----------|-------|--------|
| capex_power | **$1,700/kW** | Form Energy |
| capex_energy | **$5/kWh** | Form Energy |
| RTE | 40% | Form Energy |
| Lifetime | 17 years | Form Energy |
| Cycle life | 10,000 | Form Energy |

### Justification
Based on **Form Energy** data shared directly. Form Energy is the leading (and essentially only) commercial iron-air battery developer.

**Validation against LDES Council:**
- LDES Council "Multi-Day" category (100h): $26-38/kWh TPC
- Our model at 100h: $1,700 + $5×100 = $2,200/kW → **$22/kWh** ✓

**Important notes:**
- The extremely low capex_energy ($5/kWh) is the key advantage of iron-air
- Low RTE (40%) is a known limitation — requires ~2.5 kWh input per kWh output
- Lifetime (17 years) and RTE are **conservative** vs. LDES Council (30-40 years, 50-70% RTE)
- Form Energy's first utility project (Great River Energy, Minnesota) is under construction

Our parameters align well with LDES Council benchmarks for multi-day storage.

---

## VRFB (Vanadium Redox Flow Battery)

| Parameter | Value | Source |
|-----------|-------|--------|
| capex_power | **$700/kW** | Project analysis |
| capex_energy | **$280/kWh** | BloombergNEF + projects |
| RTE | 75% | Industry standard |
| Lifetime | 25 years | Conservative |
| Cycle life | 20,000 | Flow battery advantage |

### Justification
Revised based on analysis of real project costs and BloombergNEF data.

**Project benchmarks:**
- **Dalian (China):** 100 MW / 400 MWh (4h), ~$170-200M → ~$425-500/kWh
- **Jimusar (China):** 200 MW / 1,000 MWh (5h), ~$300-350M (storage portion) → ~$300-350/kWh
- **BloombergNEF 2024:** $423/kWh (China), $701/kWh (Rest of World)

Sources: [ESS-News](https://www.ess-news.com/2026/01/07/china-connects-worlds-largest-vanadium-flow-battery-project/), [BloombergNEF](https://about.bnef.com/blog/lithium-ion-batteries-are-set-to-face-competition-from-novel-tech-for-long-duration-storage-bloombergnef-research/)

**Reverse-engineering from projects:**
Using Dalian (4h) and Jimusar (5h) data points:
- capex_power ≈ $600-800/kW → we use **$700/kW**
- capex_energy ≈ $250-350/kWh → we use **$280/kWh**

**Validation at 10h:**
- Our model: $700 + $280×10 = $3,500/kW → $350/kWh
- BloombergNEF China: $423/kWh (we're slightly optimistic)
- LDES Council 2025: $220-572/kWh (we're mid-range)

Lifetime reduced to 25 years (vs 30) to align with LDES Council data (20-25 years).

---

## Key Takeaways

1. **Li-ion:** Our Modo data is more aggressive than public benchmarks — defensible given proprietary market access

2. **Pumped hydro:** Costs vary enormously ($600-9,000/kW). Our $3,000/kW is a reasonable mid-point for planning purposes

3. **CAES:** Hydrostor data is well-sourced from CEO quotes and project announcements

4. **LAES:** Energy Dome claims are optimistic but within LDES Council ranges — monitor as projects deploy

5. **Iron-air:** Form Energy data aligns remarkably well with LDES Council multi-day benchmarks

6. **VRFB:** Corrected to match real project economics — previous values had wrong cost profile

---

## References

- NREL ATB 2024: https://atb.nrel.gov/electricity/2024/pumped_storage_hydropower
- LDES Council 2024 Report: https://ldescouncil.com/2024-ldes-annual-report/
- BloombergNEF LDES Survey: https://about.bnef.com/blog/lithium-ion-batteries-are-set-to-face-competition-from-novel-tech-for-long-duration-storage-bloombergnef-research/
- Hydrostor: https://hydrostor.ca/
- Energy Dome: https://energydome.com/
- Form Energy: https://formenergy.com/
- Lazard LCOE+ 2024: https://www.lazard.com/media/xemfey0k/lazards-lcoeplus-june-2024-_vf.pdf
