import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the GhostNet evidence trail", () => {
    render(<App />);
    expect(screen.getAllByText(/GhostNet/).length).toBeGreaterThan(0);
    expect(screen.getByText("Fake systems. Real signals.")).toBeInTheDocument();
    expect(screen.getByText(/Synthetic evidence, labelled as such/i)).toBeInTheDocument();
  });

  it("classifies the credential stuffing preset", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole("button", { name: "Credential stuffing" }));
    expect(screen.getAllByText("credential_stuffing").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/T1110.004/).length).toBeGreaterThan(0);
  });
});
