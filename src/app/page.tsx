"use client";

import { useEffect, useState } from "react";

type Player = {
  name: string;
  salary: number;
};

type PayrollResponse = {
  team: {
    id: string;
    name: string;
  };
  season: string;
  players: Player[];
  totals: {
    team_salary: number;
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
    ["Team salary", data.totals.team_salary],
    ["Salary cap", data.totals.salary_cap],
    ["Cap space", data.totals.cap_space],
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

          <div className="mt-4 overflow-hidden rounded-xl border border-gray-800">
            {data.players.map((player) => (
              <div
                key={player.name}
                className="flex justify-between border-b border-gray-800 bg-gray-900 px-5 py-4 last:border-b-0"
              >
                <span>{player.name}</span>
                <span className="font-medium">
                  {formatCurrency(player.salary)}
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}