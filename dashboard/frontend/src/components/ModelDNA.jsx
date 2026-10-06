export default function ModelDNA({ model }) {
  if (!model) return null;
  const hex = model.hash.replace(/[^0-9a-f]/gi, "");
  const bars = hex.match(/.{1,2}/g) || [];
  return (
    <section className="panel" id="model">
      <h2>Model fingerprint</h2>
      <svg viewBox={`0 0 ${bars.length * 10} 44`} className="dna" preserveAspectRatio="none" role="img" aria-label="Visual of the model hash">
        {bars.map((b, i) => {
          const v = parseInt(b.padEnd(2, "0"), 16) / 255;
          return <rect key={i} x={i * 10 + 1} y={44 - (10 + v * 34)} width="8" height={10 + v * 34} rx="2" fill={`hsl(${176 - v * 20} ${35 + v * 25}% ${28 + v * 22}%)`} />;
        })}
      </svg>
      <dl className="kv">
        <dt>SHA-256</dt><dd className="hash">{model.hash}</dd>
        <dt>Format</dt><dd>{model.format}</dd>
        <dt>Source</dt><dd>{model.source}, runs {model.execution.toLowerCase()}</dd>
        <dt>Integrity</dt><dd>{model.status}</dd>
      </dl>
    </section>
  );
}
