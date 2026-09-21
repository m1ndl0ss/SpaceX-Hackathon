# Physical inputs in the browser demo

The app accepts real-unit project descriptions, but the supplied models still consume only a generic `scale` factor, location, type, year, mitigation flags, and nearby projects. The app's physical-input mapping is an **illustrative demo assumption with no scientific calibration**. It does not add physical features to the trained models.

## Conversion

For each field shown for a project type, divide the entered value by its reference value below. Average the ratios, then limit the result to the model's supported range, 0.4–2.0. The form and saved results disclose when that limit is applied. All six model outputs use the same derived factor. This cannot isolate the effect of water, land, or power on a particular outcome.

The references are product-demo choices, not typical project sizes, regulatory thresholds, engineering standards, or values learned from the training data. They are defined in `src/js/project-inputs.js` and versioned as `demo-mean-v1`.

| Project | Illustrative reference quantities |
|---|---|
| Wind | 30 MW generation; 6 ha occupied by infrastructure |
| Solar | 50 MW generation; 60 ha footprint; 20 m³/day freshwater withdrawal |
| Industrial | 20 MW electricity demand; 15 ha footprint; 1,000 m³/day freshwater withdrawal |
| Highway | 10 km length; 30 ha footprint |
| Housing | 200 homes; 10 ha footprint; 100 m³/day freshwater withdrawal |
| Dam | 20 MW generation; 100 ha reservoir; 50 m³/s turbine flow |
| Power line | 20 km length; 60 ha corridor |
| Data centre | 80 MW electricity demand; 24 ha footprint; 1,200 m³/day freshwater withdrawal |

For example, a data centre with 80 MW, 24 ha, and 2,400 m³/day maps to `(1 + 1 + 2) / 3 = 1.3333×`. It does not represent a separately calibrated water-temperature response. Zero freshwater withdrawal is allowed and contributes a zero ratio; it does not guarantee a zero river-warming estimate. A 10× reference project is limited to 2× with a visible warning, not extrapolated silently.

Smaller, reference, and larger example presets use 0.5×, 1×, and 1.5× of these reference quantities. Enter custom values at any time. All physical inputs describe the project before the selected mitigation; both model comparison requests use the same derived scale, changing only the mitigation flags.

## Units and persistence

- Units are converted exactly to the canonical units above: 1,000 kW = 1 MW, 10,000 m² = 1 ha, 1,000 L = 1 m³, and 1,000 m = 1 km. Changing the unit selector converts the displayed number while preserving its quantity.
- Water withdrawal is average daily operating intake, which differs from consumption or water returned to a river. Dam flow is expressed per second and has its own field.
- Positive finite values are required for size/capacity/flow fields; water withdrawal can be zero, and home counts must be whole numbers. Missing fields are not treated as zero in the physical-input mode.
- Saved assessments retain canonical physical quantities, the mapping version, reference values, calculated factor, applied factor, and exact results. Loading restores those inputs; rerunning uses the current mapping.
- Legacy assessments open in manual-factor mode with empty physical fields. In manual mode, any entered physical quantities are saved as project details and do not influence predictions.

For credible real-world estimates, the model pipeline must be extended and calibrated against suitable observations or independently validated process models. This UI conversion does not satisfy that requirement. The [model review](MODEL_REVIEW.md) describes the remaining limitations.
