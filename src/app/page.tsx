"use client";

import { FormEvent,useEffect, useState } from "react";

type Player = {
  id: number;
  name: string;
  position: string | null;
  age: number | null;
  contract_type: string | null;
  base_salary: number;
  cap_hit: number;
  guaranteed_amount: number | null;
  option_type: string | null;
};

type PayrollResponse = {
  team: {
    id: string;
    name: string;
  };
  season: string;
  players: Player[];
  totals: {
    //team_salary: number;
    total_cap_hit: number;
    total_base_salary: number;
    salary_cap: number;
    cap_space: number;
    luxury_tax: number;
    tax_room: number;
    first_apron: number;
    first_apron_room: number;
    second_apron: number;
    second_apron_room: number;
  };
  is_sample_data: boolean;
};

type SigningCalculation = {
  current_cap_hit: number;
  added_cap_hit: number;
  projected_cap_hit: number;
  salary_cap_balance: number;
  tax_room: number;
  first_apron_room: number;
  second_apron_room: number;
  over_salary_cap: boolean;
  over_luxury_tax: boolean;
  over_first_apron: boolean;
  over_second_apron: boolean;
};

type SigningScenarioResponse = {
  team: {
    id: string;
    name: string;
    abbreviation: string;
  };
  season: string;
  proposed_player: {
    name: string;
    cap_hit: number;
  };
  calculation: SigningCalculation;
  legal_analysis: {
    status: string;
    message: string;
  };
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function Home() {
  const [data, setData] = useState<PayrollResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [playerName, setPlayerName] = useState("");
  const [salaryInput, setSalaryInput] = useState("");
  const [scenarioResult, setScenarioResult] =
  useState<SigningScenarioResponse | null>(null);
  const [scenarioError, setScenarioError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const apiUrl =
      process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

    async function loadPayroll() {
      try {
        const response = await fetch(`${apiUrl}/teams/nyk/payroll`);

        if (!response.ok) {
          throw new Error(`API returned status ${response.status}`);
        }

        const payroll: PayrollResponse = await response.json();
        setData(payroll);
      } catch (requestError) {
        const message =
          requestError instanceof Error
            ? requestError.message
            : "Unable to load payroll.";

        setError(message);
      }
    }

    loadPayroll();
  }, []);

  async function handleScenarioSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
  
    setScenarioError(null);
    setScenarioResult(null);
  
    const capHit = Number(salaryInput.replace(/[$,\s]/g, ""));
  
    if (!playerName.trim()) {
      setScenarioError("Enter a player name.");
      return;
    }
  
    if (!Number.isFinite(capHit) || capHit <= 0) {
      setScenarioError("Enter a valid positive salary.");
      return;
    }
  
    setIsSubmitting(true);
  
    try {
      const apiUrl =
        process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  
      const response = await fetch(
        `${apiUrl}/teams/nyk/scenarios/signing`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            player_name: playerName.trim(),
            cap_hit: capHit,
            season: data?.season ?? "2026-27",
          }),
        },
      );
  
      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }
  
      const result: SigningScenarioResponse = await response.json();
      setScenarioResult(result);
    } catch (requestError) {
      setScenarioError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to run the scenario.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (error) {
    return (
      <main className="min-h-screen bg-gray-950 p-8 text-white">
        <h1 className="text-3xl font-bold">NBA Cap Tool</h1>
        <p className="mt-6 text-red-400">Backend error: {error}</p>
        <p className="mt-2 text-gray-400">
          Make sure FastAPI is running on port 8000.
        </p>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="min-h-screen bg-gray-950 p-8 text-white">
        Loading payroll…
      </main>
    );
  }

  const summaryItems = [
    ["Total cap hit", data.totals.total_cap_hit],
    ["Total base salary", data.totals.total_base_salary],
    ["Salary cap", data.totals.salary_cap],
    ["Basic cap balance", data.totals.cap_space],
    ["Luxury-tax line", data.totals.luxury_tax],
    ["Tax room", data.totals.tax_room],
    ["First-apron room", data.totals.first_apron_room],
    ["Second-apron room", data.totals.second_apron_room],
  ] as const;

  return (
    <main className="min-h-screen bg-gray-950 px-6 py-12 text-white">
      <div className="mx-auto max-w-5xl">
        <p className="text-sm font-semibold uppercase tracking-widest text-blue-400">
          NBA Cap Tool
        </p>

        <h1 className="mt-2 text-4xl font-bold">{data.team.name}</h1>
        <p className="mt-2 text-gray-400">{data.season}</p>

        {data.is_sample_data && (
          <div className="mt-6 rounded-lg border border-yellow-700 bg-yellow-950 p-4 text-yellow-200">
            This page currently uses placeholder contract and cap data.
          </div>
        )}

        <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {summaryItems.map(([label, value]) => (
            <div
              key={label}
              className="rounded-xl border border-gray-800 bg-gray-900 p-5"
            >
              <p className="text-sm text-gray-400">{label}</p>
              <p className="mt-2 text-2xl font-semibold">
                {formatCurrency(value)}
              </p>
            </div>
          ))}
        </section>

        <section className="mt-10">
  <h2 className="text-2xl font-semibold">Roster</h2>

  <div className="mt-4 overflow-x-auto rounded-xl border border-gray-800">
    <table className="w-full min-w-[850px] bg-gray-900">
      <thead className="border-b border-gray-700 text-left text-sm text-gray-400">
        <tr>
          <th className="px-5 py-4">Player</th>
          <th className="px-5 py-4">Pos</th>
          <th className="px-5 py-4">Age</th>
          <th className="px-5 py-4">Type</th>
          <th className="px-5 py-4 text-right">Cap hit</th>
          <th className="px-5 py-4 text-right">Base salary</th>
        </tr>
      </thead>

      <tbody>
        {data.players.map((player) => (
          <tr
            key={player.id}
            className="border-b border-gray-800 last:border-b-0"
          >
            <td className="px-5 py-4 font-medium">
              {player.name}
            </td>

            <td className="px-5 py-4 text-gray-300">
              {player.position ?? "—"}
            </td>

            <td className="px-5 py-4 text-gray-300">
              {player.age ?? "—"}
            </td>

            <td className="px-5 py-4 text-gray-300">
              {player.contract_type ?? "—"}
            </td>

            <td className="px-5 py-4 text-right font-medium">
              {formatCurrency(player.cap_hit)}
            </td>

            <td className="px-5 py-4 text-right text-gray-300">
              {formatCurrency(player.base_salary)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
</section>
<section className="mt-12">
  <h2 className="text-2xl font-semibold">Signing Scenario</h2>

  <p className="mt-2 text-gray-400">
    Add a proposed player cap hit to see the payroll impact.
  </p>

  <form
    onSubmit={handleScenarioSubmit}
    className="mt-5 rounded-xl border border-gray-800 bg-gray-900 p-6"
  >
    <div className="grid gap-5 md:grid-cols-2">
      <label className="block">
        <span className="text-sm text-gray-400">Player name</span>
        <input
          value={playerName}
          onChange={(event) => setPlayerName(event.target.value)}
          placeholder="Example: Test Free Agent"
          className="mt-2 w-full rounded-lg border border-gray-700 bg-gray-950 px-4 py-3 outline-none focus:border-blue-500"
        />
      </label>

      <label className="block">
        <span className="text-sm text-gray-400">Proposed cap hit</span>
        <input
          value={salaryInput}
          onChange={(event) => setSalaryInput(event.target.value)}
          placeholder="Example: 10000000"
          inputMode="numeric"
          className="mt-2 w-full rounded-lg border border-gray-700 bg-gray-950 px-4 py-3 outline-none focus:border-blue-500"
        />
      </label>
    </div>

    <button
      type="submit"
      disabled={isSubmitting}
      className="mt-5 rounded-lg bg-blue-600 px-5 py-3 font-semibold hover:bg-blue-500 disabled:opacity-50"
    >
      {isSubmitting ? "Calculating…" : "Simulate signing"}
    </button>

    {scenarioError && (
      <p className="mt-4 text-red-400">{scenarioError}</p>
    )}
  </form>

  {scenarioResult && (
    <div className="mt-6 rounded-xl border border-gray-800 bg-gray-900 p-6">
      <h3 className="text-xl font-semibold">
        Add {scenarioResult.proposed_player.name}
      </h3>

      <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <p className="text-sm text-gray-400">Added cap hit</p>
          <p className="mt-1 text-xl font-semibold">
            {formatCurrency(
              scenarioResult.calculation.added_cap_hit,
            )}
          </p>
        </div>

        <div>
          <p className="text-sm text-gray-400">Projected cap hit</p>
          <p className="mt-1 text-xl font-semibold">
            {formatCurrency(
              scenarioResult.calculation.projected_cap_hit,
            )}
          </p>
        </div>

        <div>
          <p className="text-sm text-gray-400">Second-apron room</p>
          <p className="mt-1 text-xl font-semibold">
            {formatCurrency(
              scenarioResult.calculation.second_apron_room,
            )}
          </p>
        </div>
      </div>

      <div className="mt-6 rounded-lg border border-yellow-800 bg-yellow-950 p-4 text-yellow-200">
        {scenarioResult.legal_analysis.message}
      </div>
    </div>
  )}
</section>
      </div>
    </main>
  );
}