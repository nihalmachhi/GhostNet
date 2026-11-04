import results from "../data/results.generated.json";
import { content } from "../data/content";

interface LabelResult {
  label: string;
  precision: number;
  recall: number;
  f1: number;
  support: number;
}

interface Report {
  data_kind: string;
  scenarios: number;
  accuracy: number;
  macro_f1: number;
  containment: { passed: boolean; failures: string[] };
  labels: LabelResult[];
  boundary_case: { scenario: string; expected: string; predicted: string; rule_id: string };
}

const report = results as Report;

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function Results() {
  const values: Record<string, string> = {
    accuracy: percent(report.accuracy),
    macro_f1: percent(report.macro_f1),
    containment: report.containment.passed ? "pass" : "fail",
  };
  const widths: Record<string, string> = {
    accuracy: percent(report.accuracy),
    macro_f1: percent(report.macro_f1),
    containment: report.containment.passed ? "100%" : "0%",
  };

  return (
    <section className="sec" id="results">
      <div className="wrap">
        <h2>{content.results.heading}</h2>
        <p className="lead2">{content.results.intro}</p>
        <div className="rg">
          {content.results.cards.map((card, index) => (
            <div className="rc" key={card.title}>
              <h3>{card.title}</h3>
              <p>{card.copy}</p>
              <div className="tb">
                <div className="mr">
                  <span>{card.title.split(" ")[0]}</span>
                  <div className="track">
                    <div
                      className="grow"
                      style={
                        {
                          "--w": widths[card.valueKey],
                          "--c": card.color,
                          "--i": index,
                        } as React.CSSProperties
                      }
                    />
                  </div>
                  <b>{values[card.valueKey]}</b>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="sim" style={{ marginTop: 22 }}>
          <div className="shead">
            <span>{content.results.labelsTitle}</span>
            <span>
              {report.scenarios} synthetic scenarios · {report.data_kind}
            </span>
          </div>
          <div className="tb" style={{ marginTop: 14 }}>
            {report.labels.map((label) => (
              <div className="mr" key={label.label}>
                <span>{label.label}</span>
                <div className="track">
                  <div
                    className="grow"
                    style={{ "--w": percent(label.f1), "--c": label.f1 >= 0.8 ? "var(--ok)" : "var(--bad)" } as React.CSSProperties}
                  />
                </div>
                <b>{label.f1.toFixed(2)}</b>
              </div>
            ))}
          </div>
          <div className="evp">
            <b>{content.results.boundaryTitle}</b>
            <p style={{ color: "var(--mu)", marginTop: 6 }}>{content.results.boundaryCopy}</p>
            <dl>
              <dt>scenario</dt>
              <dd>{report.boundary_case.scenario}</dd>
              <dt>expected</dt>
              <dd>{report.boundary_case.expected}</dd>
              <dt>predicted</dt>
              <dd>{report.boundary_case.predicted}</dd>
              <dt>rule</dt>
              <dd>{report.boundary_case.rule_id}</dd>
            </dl>
          </div>
        </div>
        <p className="note">{content.results.note}</p>
      </div>
    </section>
  );
}
