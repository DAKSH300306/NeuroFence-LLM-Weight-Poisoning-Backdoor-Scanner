import { useEffect, useRef } from "react";
export default function ScanProgress({ state, progress, step, logs }) {
  const box = useRef(null);
  useEffect(() => { if (box.current) box.current.scrollTop = box.current.scrollHeight; }, [logs]);
  if (state === "idle" && !logs.length) return null;
  return (
    <section className="panel progress">
      <div className="row between">
        <strong>{step}</strong><span className="num">{progress}%</span>
      </div>
      <div className="bar" role="progressbar" aria-valuenow={progress} aria-valuemin="0" aria-valuemax="100">
        <i style={{ width: progress + "%" }} />
      </div>
      <div className="log" ref={box}>{logs.map((l, i) => <div key={i}>{l}</div>)}</div>
    </section>
  );
}
