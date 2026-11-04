import { Window } from "../components/Window";
import { content, DOCS, GITHUB } from "../data/content";

export function Hero() {
  return (
    <header className="hero" id="top">
      <h1>{content.hero.headline}</h1>
      <p>{content.hero.subcopy}</p>
      <div className="cta">
        <a className="pill w" href="#start">
          {content.hero.primary}
        </a>
        <a className="pill" href={DOCS}>
          {content.hero.secondary}
        </a>
        <a className="pill" href={GITHUB}>
          {content.nav.githubLabel}
        </a>
      </div>
      <div className="wrap">
        <Window />
      </div>
    </header>
  );
}
