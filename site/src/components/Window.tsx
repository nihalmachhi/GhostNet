import { useEffect, useState } from "react";
import { content } from "../data/content";
import { useTour } from "../features/tour/useTour";

const TABS = content.tour.tabs;

export function Window() {
  const { index, setIndex, paused, setPaused } = useTour(TABS.length, 7000);
  const [hover, setHover] = useState(false);
  const active = TABS[index];

  useEffect(() => {
    setPaused(hover);
  }, [hover, setPaused]);

  return (
    <div
      className="win"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onFocus={() => setHover(true)}
      onBlur={() => setHover(false)}
    >
      <aside className="side">
        <div className="dots" aria-hidden="true">
          <i />
          <i />
          <i />
        </div>
        {TABS.map((tab, i) => (
          <button
            key={tab.name}
            role="tab"
            aria-selected={i === index}
            className={i === index ? "it on" : "it"}
            onClick={() => setIndex(i)}
            onKeyDown={(event) => {
              if (event.key === "ArrowRight") setIndex((index + 1) % TABS.length);
              if (event.key === "ArrowLeft") setIndex((index - 1 + TABS.length) % TABS.length);
            }}
          >
            {tab.name}
            {i === index && !paused && <span className="bar" />}
          </button>
        ))}
        <h4>{content.tour.sideTitle}</h4>
        <div className="sp-r">
          <span className="dot" /> {content.tour.promptValue}
        </div>
        <div className="sp-r" style={{ color: "#62626b" }}>
          {content.tour.promptLabel}
        </div>
      </aside>

      <div className="main">
        <div className="col">
          <h3>{active.name}</h3>
          <p className="sub">{content.tour.promptValue}</p>
          <p className="tx">{active.copy}</p>
          <div className="term">{active.code}</div>
        </div>
        <div className="col">
          <h4 style={{ marginTop: 0 }}>{active.label}</h4>
          <div style={{ fontSize: "1.35rem", fontWeight: 600, marginBottom: 6 }}>{active.value}</div>
          <p className="sub">{active.detail}</p>
          <h4>Session</h4>
          <ul className="lst">
            {active.stats.map(([label, value]) => (
              <li key={label}>
                {label} <b style={{ float: "right" }}>{value}</b>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <button
        className="ctrl"
        onClick={() => setPaused(!paused)}
        aria-label={paused ? content.tour.resume : content.tour.pause}
        style={{ position: "absolute", right: 16, top: 16 }}
      >
        {paused ? "▶" : "❚❚"}
      </button>
    </div>
  );
}
