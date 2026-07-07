
"use client";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { reviewRepository } from "@/lib/api";
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap');
</style>



function AnalysisCard({
  title,
  review,
}: {
  title: string;
  review: any;
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
          <div
  style={{ fontFamily: "var(--font-geist-sans)" }}
  className="space-y-5 text-sm text-zinc-400"
>
  <div>
    <div className="mb-2 flex items-center gap-3">
      <span className="rounded bg-zinc-800 px-2 py-1 text-xs">
        {review.grade}
      </span>

      <span className="text-zinc-500">
        Score: {review.score ?? review.overall_score}
      </span>
    </div>

    <p className="leading-relaxed">
      {review.summary}
    </p>
  </div>

  <div>
    <h3 className="mb-2 text-zinc-100 font-medium">
      Strengths
    </h3>

    <ul className="list-disc space-y-1 pl-5">
      {(review.strengths || []).map((item: string) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  </div>

  <div>
    <h3 className="mb-2 text-zinc-100 font-medium">
      Issues
    </h3>

    <ul className="list-disc space-y-1 pl-5">
      {(
        review.issues ||
        review.critical_issues ||
        []
      ).map((item: string) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  </div>

  <div>
    <h3 className="mb-2 text-zinc-100 font-medium">
      Recommendations
    </h3>

    <ul className="list-disc space-y-1 pl-5">
      {(
        review.recommendations ||
        review.top_recommendations ||
        []
      ).map((item: string) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  </div>
</div>
        </>
      )}
    </div>
  );
}

export default function Home() {

  const [showAnalysis, setShowAnalysis] = useState(false);
  const [repoUrl, setRepoUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [review, setReview] = useState<any>(null);
  const [error, setError] = useState("");

  const handleReview = async () => {

  setError("");

  if (!repoUrl.trim()) {
    setError("Please enter a GitHub repository URL.");
    return;
  }

  const githubUrl =
    /^https:\/\/github\.com\/[^\/]+\/[^\/]+\/?$/;

  if (!githubUrl.test(repoUrl.trim())) {
    setError("Please enter a valid GitHub repository URL.");
    return;
  }

  setLoading(true);

  try {

    const response = await reviewRepository(
      repoUrl,
      false
    );

    setReview(response.data);
    setShowAnalysis(true);

  } catch (err: any) {

    setError(err.message);

  } finally {

    setLoading(false);

  }

};

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
  value={repoUrl}
  onChange={(e) => setRepoUrl(e.target.value)}
  style={{ fontFamily: "var(--font-geist-sans)" }}
  placeholder="URL - https://github.com/username/repo"
  className="w-full rounded-full border border-zinc-800 bg-black px-6 py-4 text-zinc-100 placeholder:text-zinc-600 focus:border-zinc-600 focus:outline-none"
/>
        </div>

        {error && (
  <p
    className="mt-3 text-sm text-red-500"
    style={{ fontFamily: "var(--font-geist-sans)" }}
  >
    {error}
  </p>
)}

        

        <div className="mx-auto mt-12">
          <Button
  onClick={handleReview}
  disabled={loading}
  style={{
    fontFamily: "var(--font-geist-sans)",
    fontSize: "1.5rem",
    backgroundColor: "white",
    color: "black",
    cursor: loading ? "not-allowed" : "pointer",
    padding: "1rem 1rem",
    fontWeight: 350,
  }}
>
  {loading ? (
    <div className="flex items-center gap-2">
      <Loader2 className="h-5 w-5 animate-spin" />
      Loading
    </div>
  ) : (
    "GO"
  )}
</Button>
        </div>

{showAnalysis && review && (
  <div className="mx-auto mt-24 max-w-5xl grid gap-4 text-left md:grid-cols-2">

    {[
      {
        title: "Architecture",
        review: review.architecture_review,
      },
      {
        title: "Dependencies",
        review: review.dependency_review,
      },
      {
        title: "Documentation",
        review: review.documentation_review,
      },
      {
        title: "Testing",
        review: review.testing_review,
      },
      {
        title: "Code Quality",
        review: review.codeQuality_review,
      },
    ].map(({ title, review }) => (
      <AnalysisCard
        key={title}
        title={title}
        review={review}
      />
    ))}

  </div>
)}
      </div>
    </main>
  );
}