import attackData from "./__fixtures__/attack_map.generated.json";
import rulesData from "./__fixtures__/rules.generated.json";

export type FeatureKey =
  | "n_events"
  | "n_auth"
  | "n_unique_users"
  | "n_commands"
  | "duration_s"
  | "iat_cv"
  | "has_token"
  | "exploit_paths";

export type Features = Record<FeatureKey, number | boolean>;

export type Condition = number | boolean | Record<string, number>;

export interface Rule {
  id: string;
  label: string;
  score: number;
  when: Partial<Record<FeatureKey, Condition>>;
  evidence: string[];
}

export interface Classification {
  label: string;
  rule_id: string;
  rule_score: number;
  rule_evidence: string[];
}

export interface AttackMapping {
  tactic: string;
  technique: string;
  name: string;
  evidence: string[];
}

export const RULES = rulesData as Rule[];
export const ATTACK_MAP = attackData as Record<string, AttackMapping[]>;

const OPS: Record<string, (left: number, right: number) => boolean> = {
  gte: (left, right) => left >= right,
  gt: (left, right) => left > right,
  lte: (left, right) => left <= right,
  lt: (left, right) => left < right,
  eq: (left, right) => left === right,
  ne: (left, right) => left !== right,
};

export function matches(features: Partial<Features>, condition: Partial<Record<FeatureKey, Condition>>): boolean {
  for (const [key, expected] of Object.entries(condition)) {
    const actual = features[key as FeatureKey];
    if (actual === undefined) return false;
    if (typeof expected === "object" && expected !== null) {
      if (typeof actual !== "number") return false;
      for (const [op, value] of Object.entries(expected)) {
        const compare = OPS[op];
        if (!compare || !compare(actual, value)) return false;
      }
    } else if (actual !== expected) {
      return false;
    }
  }
  return true;
}

export function classify(features: Features): Classification {
  for (const rule of RULES) {
    if (matches(features, rule.when)) {
      return {
        label: rule.label,
        rule_id: rule.id,
        rule_score: rule.score,
        rule_evidence: rule.evidence,
      };
    }
  }
  return {
    label: "benign_noise",
    rule_id: "fallback",
    rule_score: 0.1,
    rule_evidence: ["no rule matched"],
  };
}

export function attackFor(label: string): AttackMapping[] {
  return ATTACK_MAP[label] ?? [];
}

export interface ScenarioInput {
  auth: number;
  users: number;
  commands: number;
  exploits: number;
  duration: number;
  regularity: number;
  canary: boolean;
}

export function buildFeatures(input: ScenarioInput): Features {
  const n_auth = Math.max(0, Math.round(input.auth));
  const n_unique_users = Math.max(0, Math.min(n_auth, Math.round(input.users)));
  const n_commands = Math.max(0, Math.round(input.commands));
  const exploit_paths = Math.max(0, Math.round(input.exploits));
  const n_events = Math.max(1, n_auth + n_commands + exploit_paths + 1);
  return {
    n_events,
    n_auth,
    n_unique_users,
    n_commands,
    duration_s: Math.max(0, input.duration),
    iat_cv: Math.max(0, Math.min(2, (100 - input.regularity) / 100)),
    has_token: input.canary,
    exploit_paths,
  };
}

export const PRESETS: Array<{ name: string; input: ScenarioInput }> = [
  {
    name: "Credential stuffing",
    input: { auth: 5, users: 5, commands: 0, exploits: 0, duration: 4, regularity: 90, canary: false },
  },
  {
    name: "Canary follow-up",
    input: { auth: 0, users: 0, commands: 0, exploits: 0, duration: 1, regularity: 90, canary: true },
  },
  {
    name: "Exploit probe",
    input: { auth: 0, users: 0, commands: 0, exploits: 1, duration: 4, regularity: 40, canary: false },
  },
  {
    name: "Scripted commands",
    input: { auth: 0, users: 0, commands: 4, exploits: 0, duration: 6, regularity: 95, canary: false },
  },
  {
    name: "Benign noise",
    input: { auth: 0, users: 0, commands: 0, exploits: 0, duration: 4, regularity: 40, canary: false },
  },
];
