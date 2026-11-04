export const faq = [
  {
    q: "Is it safe to run?",
    a: "In a local lab, yes. The decoys are inert, sit on an internal-only network and never connect back to a client. Do not expose the ports or run it on a network you do not own.",
  },
  {
    q: "What is actually stored about a login attempt?",
    a: "A keyed username hash, username length and class, password length, a keyed password hash and a coarse category. Raw usernames and passwords are never written.",
  },
  {
    q: "What does tamper-evident mean here?",
    a: "Each decoy has an HMAC-SHA256 chain: every event covers the previous hash and its canonical body. A signed checkpoint records the head of each chain. A database writer can still rewrite a whole chain, so this detects casual edits rather than making them impossible.",
  },
  {
    q: "Are the ATT&CK labels certain?",
    a: "No. They are ordered heuristic rules with an explicit score and evidence. The mapping is tactic and technique level, with no attribution or campaign claim.",
  },
  {
    q: "Why can a decoy not reach the internet?",
    a: "Decoys are attached only to the internal deception network. The edge proxy is the single dual-homed service and forwards only the three decoy ports.",
  },
  {
    q: "Can the admin API be reached from a decoy?",
    a: "No. The admin API is attached only to the control network and published on loopback. The containment checker rejects a configuration that puts it on the deception network.",
  },
  {
    q: "What does the bandit actually do?",
    a: "An epsilon-greedy selector chooses among allowlisted proposal kinds. The proposal is stored with a TTL. An analyst approval records a decision and never deploys a change.",
  },
  {
    q: "Are the evaluation numbers real?",
    a: "They are real outputs from a deterministic synthetic run, but they are not evidence of real-world detection quality. The report is labelled synthetic and includes a deliberate rule-boundary miss.",
  },
  {
    q: "Is it production ready?",
    a: "No. It is a local learning project. There is no public deployment configuration, no high-interaction service, no malware capture and no per-analyst identity model.",
  },
];
