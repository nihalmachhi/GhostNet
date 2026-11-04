import { content, GITHUB } from "../data/content";

const stages = content.cta.stages;
const boxWidth = 112;
const gap = 30;
const width = stages.length * boxWidth + (stages.length - 1) * gap;

export function Cta() {
  return (
    <section className="cta2" aria-label="Get started">
      <div className="wrap">
        <div className="archw">
          <svg
            className="flow arch"
            viewBox={`0 0 ${width} 90`}
            role="img"
            aria-label="GhostNet pipeline"
            style={{ width: "100%", minWidth: 820, maxWidth: width, height: "auto", overflow: "visible" }}
          >
            {stages.map((_, index) => {
              if (index === stages.length - 1) return null;
              const x1 = index * (boxWidth + gap) + boxWidth;
              const x2 = x1 + gap;
              return (
                <path
                  key={index}
                  className="fl"
                  d={`M${x1} 45H${x2}`}
                  style={{
                    fill: "none",
                    stroke: "#5a5a64",
                    strokeWidth: 1.2,
                    strokeDasharray: "4 4",
                    animation: "dash 1.2s linear infinite",
                  }}
                />
              );
            })}
            {stages.map((stage, index) => {
              const x = index * (boxWidth + gap);
              const last = index === stages.length - 1;
              return (
                <g
                  key={stage}
                  className={`gn st ${last ? "last" : ""}`}
                  style={{
                    animation: `${last ? "stlb" : "stl"} 6.3s ease-in-out infinite`,
                    animationDelay: `${index * 0.9}s`,
                  }}
                >
                  <rect x={x} y={12} width={boxWidth} height={66} rx={9} style={{ fill: "#19191c", stroke: "#242428" }} />
                  <text textAnchor="middle" style={{ font: "500 10px var(--fm)", fill: "#ececee" }}>
                    {stage.split(" ").map((word, wordIndex, words) => (
                      <tspan
                        key={word}
                        x={x + boxWidth / 2}
                        y={12 + 30 + (wordIndex - (words.length - 1) / 2) * 13}
                      >
                        {word}
                      </tspan>
                    ))}
                  </text>
                </g>
              );
            })}
            <circle r={3.2} fill="#f4f4f5">
              <animateMotion dur="6.3s" repeatCount="indefinite" path={`M0 45H${width}`} />
            </circle>
          </svg>
        </div>
        <h2>{content.cta.heading}</h2>
        <p className="lead2" style={{ margin: "14px auto 0" }}>
          {content.cta.copy}
        </p>
        <div className="btns">
          <a className="pill w" href={GITHUB}>
            {content.cta.primary}
          </a>
          <a className="pill" href="#start">
            {content.cta.secondary}
          </a>
        </div>
      </div>
    </section>
  );
}
