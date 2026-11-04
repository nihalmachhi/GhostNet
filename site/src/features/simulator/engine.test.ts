import { describe, it, expect } from "vitest";
import classification from "./__fixtures__/classification.json";
import { attackFor, buildFeatures, classify, matches, PRESETS, RULES } from "./engine";

describe("rule parity with Python", () => {
  for (const item of classification) {
    it(item.name, () => {
      const got = classify(item.features);
      expect(got.label).toBe(item.expected.label);
      expect(got.rule_id).toBe(item.expected.rule_id);
      expect(got.rule_score).toBeCloseTo(item.expected.rule_score, 6);
      expect(got.rule_evidence).toEqual(item.expected.rule_evidence);
    });
  }
});

describe("rule engine", () => {
  it("keeps the ordered rule set in sync with YAML", () => {
    expect(RULES[0].id).toBe("canary_followup");
    expect(RULES[RULES.length - 1].id).toBe("benign_noise");
  });

  it("evaluates comparison operators", () => {
    expect(matches({ n_auth: 4, has_token: false }, { n_auth: { gte: 4 } })).toBe(true);
    expect(matches({ n_auth: 3, has_token: false }, { n_auth: { gte: 4 } })).toBe(false);
    expect(matches({ n_auth: 3, has_token: true }, { has_token: true })).toBe(true);
  });

  it("maps observed labels to ATT&CK rows", () => {
    expect(attackFor("credential_stuffing")[0].technique).toBe("T1110.004");
    expect(attackFor("scripted_interaction")).toEqual([]);
  });

  it("builds bounded features from sliders", () => {
    const features = buildFeatures({
      auth: 6,
      users: 20,
      commands: 2,
      exploits: 0,
      duration: 9,
      regularity: 100,
      canary: false,
    });
    expect(features.n_unique_users).toBe(6);
    expect(features.iat_cv).toBe(0);
    expect(features.n_events).toBe(9);
  });

  it("ships presets that exercise distinct labels", () => {
    const labels = new Set(PRESETS.map((preset) => classify(buildFeatures(preset.input)).label));
    expect(labels).toContain("credential_stuffing");
    expect(labels).toContain("canary_followup");
    expect(labels).toContain("scripted_interaction");
  });
});
