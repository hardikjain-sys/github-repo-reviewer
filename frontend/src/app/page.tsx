
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";

<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap');
</style>



function AnalysisCard({
  title,
  body,
}: {
  title: string;
  body: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div
      onClick={() => setOpen(!open)}
      className={`cursor-pointer rounded-2xl border p-6 transition-all duration-200 ${
        open
          ? "border-zinc-700 bg-white/5"
          : "border-zinc-800 bg-white/[0.02] hover:border-zinc-700 hover:bg-white/[0.04]"
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          
          <h2 style={{ fontFamily: "var(--font-geist-sans)" }} className="text-base font-medium text-zinc-100">{title}</h2>
        </div>
        <span
          className={`text-zinc-500 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        >
          ▾
        </span>
      </div>

      {open && (
        <>
          <div className="my-4 h-px bg-zinc-800" />
          <p style={{ fontFamily: "var(--font-geist-sans)" }} className="text-sm leading-relaxed text-zinc-500">{body}</p>
        </>
      )}
    </div>
  );
}

export default function Home() {

  const [showAnalysis, setShowAnalysis] = useState(false);
  const [deepAnalysis, setDeepAnalysis] = useState(false);

  return (
    <main className="grid-bg min-h-screen bg-black px-6 py-32">
      <div className="mx-auto w-full text-center">
        <h1
          className="md:text-7xl tracking-[-0.09em] text-zinc-50"
          style={{ fontFamily: "var(--font-geist-sans)" }}
        >
          Repository Reviewer
        </h1>

        <p
          className="mx-auto mt-8 max-w-2xl text-lg leading-8 text-zinc-500"
          style={{ fontFamily: "var(--font-geist-sans)" }}
        >
          Analyze architecture, dependencies, documentation, testing and code
          quality.
        </p>

        <div className="mx-auto mt-12 max-w-3xl">
          <input
            type="text"
            style={{ fontFamily: "var(--font-geist-sans)" }}
            placeholder="URL - https://github.com/username/repo"
            className="w-full rounded-full border border-zinc-800 bg-black px-6 py-4 text-zinc-100 placeholder:text-zinc-600 focus:border-zinc-600 focus:outline-none"
          />
        </div>

        <div className="mt-6 flex items-center justify-center gap-3">
  <Switch
    checked={deepAnalysis}
    onCheckedChange={setDeepAnalysis}
  />

  <span
    className="text-sm text-zinc-400"
    style={{ fontFamily: "var(--font-geist-sans)" }}
  >
    Deep Analysis
    <span className="ml-2 text-zinc-600">
      (takes longer)
    </span>
  </span>
</div>

        <div className="mx-auto mt-12">
          <Button
            onClick={() => setShowAnalysis(true)}
            style={{
              fontFamily: "var(--font-geist-sans)",
              fontSize: "1.5rem",
              backgroundColor: "white",
              color: "black",
              cursor: "pointer",
              padding: "1rem 1rem",
              fontWeight: 350,
            }}
          >
            GO
          </Button>
        </div>

       {showAnalysis && (
  <div className="mx-auto mt-24 max-w-5xl grid gap-4 text-left md:grid-cols-2">
    {[
      {
        title: "Architecture",
        
        body: "The repository follows a modular architecture with clear separation between components, services, and utility modules.",
      },
      {
        title: "Dependencies",
        body: "The project uses several third-party libraries for routing, state management, and data processing.",
      },
      {
        title: "Documentation",
        body: "Documentation is available for setup and usage, with examples covering common workflows.",
      },
      {
        title: "Testing",
        body: "Unit tests cover the core functionality, while integration tests validate end-to-end workflows.",
      },
      {
        title: "Code Quality",
        body: "The codebase demonstrates consistent naming conventions, maintainable abstractions, and good project organization.",
      },
    ].map(({ title, body }) => (
      <AnalysisCard key={title} title={title} body={body} />
    ))}
  </div>
)}
      </div>
    </main>
  );
}