export function metrics(inputs, mitigated = false) {
  const yearFactor = 1 + (inputs.year - 2035) * 0.025;
  const cooling = mitigated || inputs.cooling;
  const buffer = mitigated || inputs.buffer;
  const temp = (inputs.water / 1200) * 1.8 * yearFactor * (cooling ? 0.28 : 1);
  const habitat =
    (inputs.land * 1.05 + inputs.water * 0.014) * yearFactor * (cooling ? 0.62 : 1) * (buffer ? 0.47 : 1);
  const stress = (inputs.water / 1200) * 12 * yearFactor * (cooling ? 0.4 : 1) * (buffer ? 0.7 : 1);
  const price = inputs.power * 0.08 * (cooling ? 1.06 : 1);
  return { temp, habitat, stress, price };
}
