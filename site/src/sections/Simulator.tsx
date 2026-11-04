import { useState } from "react";
import { content } from "../data/content";
import {
  attackFor,
  buildFeatures,
  classify,
  PRESETS,
  type ScenarioInput,
} from "../features/simulator/engine";

const copy = content.simulator;

function Slider(props: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  suffix?: string;
  onChange: (value: number) => void;
}) {
  return (
    <label style={{ display: "grid", gap: 4, marginBottom: 12 }}>
      <span>
        {props.label}: <b>{props.value}{props.suffix ?? ""}</b>
      </span>
      <input
        type="range"
        min={props.min}
        max={props.max}
        step={props.step ?? 1}
        value={props.value}
        onChange={(event) => props.onChange(Number(event.target.value))}
      />
    </label>
  );
}

export function Simulator() {
  const [input, setInput] = useState<ScenarioInput>(PRESETS[0].input);
  const features = buildFeatures(input);
  const result = classify(features);
  const attack = attackFor(result.label);
  const set = <K extends keyof ScenarioInput,>(key: K, value: ScenarioInput[K]) =>
    setInput((current) => ({ ...current, [key]: value }));

  const timeline = [
    ...Array.from({ length: Number(features.n_auth) }, () => "auth"),
    ...Array.from({ length: Number(features.n_commands) }, () => "command"),
    ...Array.from({ length: Number(features.exploit_paths) }, () => "exploit"),
    ...(input.canary ? ["canary"] : []),
    "open",
  ];

  return (
    <section className="sec" id="try">
      <div className="wrap">
        <h2>{copy.heading}</h2>
        <p className="lead2">{copy.intro}</p>
        <div className="sim">
          <div className="shead">
            <span>{copy.timeline}</span>
            <span>
              {features.n_events} {copy.events} · iat_cv {Number(features.iat_cv).toFixed(2)}
            </span>
          </div>

          <div className="stats">
            <div className="stat">
              <b>{features.n_auth}</b>
              <span>{copy.controls.auth}</span>
            </div>
            <div className="stat">
              <b>{features.n_unique_users}</b>
              <span>{copy.controls.users}</span>
            </div>
            <div className="stat">
              <b>{features.n_commands}</b>
              <span>{copy.controls.commands}</span>
            </div>
            <div className="stat">
              <b>{features.duration_s}s</b>
              <span>{copy.controls.duration}</span>
            </div>
          </div>

          <div className="scols">
            <div>
              <div className="ctl" style={{ marginBottom: 14 }}>
                {PRESETS.map((preset) => (
                  <button
                    key={preset.name}
                    className="cell"
                    onClick={() => setInput(preset.input)}
                    aria-pressed={JSON.stringify(preset.input) === JSON.stringify(input)}
                  >
                    {preset.name}
                  </button>
                ))}
              </div>
              <Slider label={copy.controls.auth} value={input.auth} min={0} max={8} onChange={(value) => set("auth", value)} />
              <Slider label={copy.controls.users} value={input.users} min={0} max={8} onChange={(value) => set("users", value)} />
              <Slider label={copy.controls.commands} value={input.commands} min={0} max={8} onChange={(value) => set("commands", value)} />
              <Slider label={copy.controls.exploits} value={input.exploits} min={0} max={3} onChange={(value) => set("exploits", value)} />
              <Slider label={copy.controls.duration} value={input.duration} min={0} max={30} onChange={(value) => set("duration", value)} />
              <Slider label={copy.controls.regularity} value={input.regularity} min={0} max={100} suffix="%" onChange={(value) => set("regularity", value)} />
              <label style={{ display: "flex", gap: 8, alignItems: "center", color: "var(--mu)", fontSize: "0.85rem" }}>
                <input
                  type="checkbox"
                  checked={input.canary}
                  onChange={(event) => set("canary", event.target.checked)}
                />
                {copy.controls.canary}
              </label>
            </div>

            <div>
              <div className="term" style={{ marginTop: 0 }}>
                <div style={{ color: "var(--fg)", fontSize: "1.1rem", marginBottom: 4 }}>{result.label}</div>
                <div>{copy.result.rule}: {result.rule_id}</div>
                <div>{copy.result.score}: {result.rule_score.toFixed(2)}</div>
                <div style={{ marginTop: 8 }}>{copy.result.evidence}: {result.rule_evidence.join("; ")}</div>
              </div>

              <div style={{ marginTop: 14 }}>
                {timeline.map((kind, index) => (
                  <span
                    key={`${kind}-${index}`}
                    className="chip"
                    style={{
                      borderColor:
                        kind === "auth"
                          ? "#f59e0b"
                          : kind === "command"
                            ? "#22c55e"
                            : kind === "exploit"
                              ? "#ef4444"
                              : kind === "canary"
                                ? "#8b5cf6"
                                : "#242428",
                      color: "var(--mu)",
                    }}
                  >
                    {kind}
                  </span>
                ))}
              </div>

              <div className="evp">
                <b>{copy.result.attack}</b>
                {attack.length === 0 ? (
                  <p style={{ color: "var(--mu)", marginTop: 6 }}>{copy.result.noAttack}</p>
                ) : (
                  <dl>
                    {attack.map((row) => (
                      <div key={row.technique} style={{ display: "contents" }}>
                        <dt>{row.technique}</dt>
                        <dd>
                          {row.tactic} · {row.name}
                        </dd>
                      </div>
                    ))}
                  </dl>
                )}
              </div>
            </div>
          </div>
          <p className="note" style={{ textAlign: "left", margin: "18px 0 0" }}>
            {copy.result.note}
          </p>
        </div>
      </div>
    </section>
  );
}
