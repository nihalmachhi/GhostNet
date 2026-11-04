import { content, DOCS, GITHUB } from "../data/content";

function hrefFor(label: string): string {
  if (label === "GitHub") return GITHUB;
  if (label === "Docs" || label === "Limitations") return DOCS;
  if (label === "Issues") return `${GITHUB}/issues`;
  if (label === "MIT License") return `${GITHUB}/blob/main/LICENSE`;
  const links = content.nav.links;
  return links.find((link) => link.label === label)?.href ?? "#top";
}

export function Footer() {
  return (
    <footer className="wrap">
      <div className="foot">
        <div className="fcols">
          <div>
            <a className="brand" href="#top">
              GhostNet
            </a>
            <p className="tg">{content.footer.blurb}</p>
          </div>
          {content.footer.columns.map((column, index) => (
            <div key={index}>
              <h5>{["Product", "Run it", "Source"][index]}</h5>
              <ul>
                {column.map((item) => (
                  <li key={item}>
                    <a href={hrefFor(item)}>{item}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="fbot">
          <span>{content.footer.note}</span>
          <span>Python · SQLite · HMAC-SHA256 · MIT License</span>
        </div>
        <div className="mark" aria-hidden="true">
          GhostNet
        </div>
      </div>
    </footer>
  );
}
