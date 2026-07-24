## Municipal Wastewater Treatment & Water Reuse System Simulator

A Python-based simulation of a municipal wastewater treatment train that models preliminary treatment, primary clarification, activated sludge (secondary treatment), tertiary polishing, and chlorination-based disinfection using established wastewater engineering design equations and mass balances.

The model tracks water quality (BOD, TSS, TP, TN, and E. coli) through each treatment stage, estimates sludge production and oxygen demand, and evaluates the final effluent against U.S. EPA irrigation water reuse guidelines.

I built this as a way of trying to incorporate what I learned in my Environmental Engineering Systems class into a real world application instead of just theory.  I wanted to incorporate engineering equations including Monod kinetics for activated sludge, mass-balance sludge production, hydraulic retention time (HRT), food-to-microorganism (F/M) ratio, oxygen demand, Henry's Law for dissolved oxygen saturation, and first-order chlorination kinetics, and then  validate the model against published operating data from a real municipal treatment plant.

## What it models

| Treatment Stage | Engineering Approach |
|-----------------|----------------------|
| Preliminary treatment | Screening and grit removal using representative TSS removal |
| Primary clarification | BOD, TSS, and TP removal with primary sludge mass balance |
| Secondary treatment | Activated sludge modeled using Monod kinetics (CSTR), biomass yield, oxygen demand, HRT, and F/M ratio |
| Tertiary treatment | Filtration and nutrient polishing using representative removal efficiencies |
| Disinfection | First-order chlorine inactivation of *E. coli* based on hydraulic contact time |
| Sludge production | Combined primary, biological, and chemical sludge estimate |

## Output
Running the model will generate the following report: 

## Output

Running the model will generate the following report:

```text
WASTEWATER TREATMENT REPORT

Concentrations at each stage:

Influent
  BOD: 287 mg/L
  TSS: 262 mg/L
  TP : 5.3 mg/L
  TN : 32.2 mg/L
  E.coli: 10000000.0

After Preliminary
  BOD: 287 mg/L
  TSS: 235.8 mg/L
  TP : 5.3 mg/L
  TN : 32.2 mg/L
  E.coli: 10000000.0

After Primary
  BOD: 200.9 mg/L
  TSS: 106.11 mg/L
  TP : 4.77 mg/L
  TN : 32.2 mg/L
  E.coli: 10000000.0

After Secondary
  BOD: 3.94 mg/L
  TSS: 15.92 mg/L
  TP : 3.82 mg/L
  TN : 22.54 mg/L
  E.coli: 10000000.0

After Tertiary
  BOD: 3.94 mg/L
  TSS: 6.37 mg/L
  TP : 0.57 mg/L
  TN : 6.76 mg/L
  E.coli: 10000000.0

After Disinfection
  BOD: 3.94 mg/L
  TSS: 6.37 mg/L
  TP : 0.57 mg/L
  TN : 6.76 mg/L
  E.coli: 40.65

Design Parameters
HRT: 0.5 days
F/M Ratio: 0.135
MLSS: 3000 mg/L
Oxygen Required: 9303.5 kg/day
Oxygen supply needed: 12404.6 kg/day

Sludge Production
Primary: 6845.4 kg/day
Biological: 4214.6 kg/day
Chemical: 513.6 kg/day
Total: 11573.6 kg/day

Final Effluent Check
BOD : PASS
TSS : PASS
TP : PASS
TN : PASS
E_coli : PASS

Removal Efficiencies
BOD Removal: 98.6 %
TSS Removal: 97.6 %
TN Removal: 79.0 %
TP Removal: 89.2 %
```
### Figure 1. Pollutant concentration through the treatment train

![Figure 1 – Treatment train results](Figure_1.png)

### Figure 2. Simulated daily sludge production

![Figure 2 – Sludge production breakdown](Figure_2.png)

