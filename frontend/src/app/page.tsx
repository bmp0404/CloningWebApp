"use client";

import { useState } from "react";
import Image from "next/image";

export default function Home() {
  const [url, setUrl] = useState("");
  const [html, setHtml] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClone = async () => {
    if (!url) return;
    setLoading(true);
    setError(null);
    setHtml(null);

    try {
      const res = await fetch("http://localhost:8000/clone", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!res.ok) {
        const { detail } = await res.json();
        throw new Error(detail ?? "Clone failed");
      }

      const data = await res.json();
      setHtml(data.html);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-rows-[auto_1fr_auto] items-center justify-items-center min-h-screen p-8 gap-12 font-[family-name:var(--font-geist-sans)]">
      {/* ---------- Header ---------- */}
      <header className="flex flex-col items-center gap-4">
        <Image
          className="dark:invert"
          src="/next.svg"
          alt="Next.js logo"
          width={120}
          height={26}
          priority
        />
        <h1 className="text-xl font-semibold">Website Cloner</h1>
      </header>

      {/* ---------- Main ---------- */}
      <main className="w-full max-w-3xl flex flex-col gap-6">
        {/* Input + button */}
        <div className="flex gap-2">
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            className="flex-1 border rounded px-3 py-2 text-sm dark:bg-[#1a1a1a]"
          />
          <button
            onClick={handleClone}
            disabled={loading}
            className="bg-black dark:bg-white text-white dark:text-black px-4 py-2 rounded disabled:opacity-40"
          >
            {loading ? "Cloning…" : "Clone"}
          </button>
        </div>

        {/* Error message */}
        {error && (
          <p className="text-red-500 text-sm">{error}</p>
        )}

        {/* Result iframe */}
        {html && (
          <iframe
            srcDoc={html}
            className="w-full h-[70vh] border rounded"
          />
        )}

        {/* Simple placeholder when nothing yet */}
        {!html && !loading && !error && (
          <p className="text-center text-sm opacity-60">
            Enter a public URL and click <strong>Clone</strong>.
          </p>
        )}
      </main>

      {/* ---------- Footer ---------- */}
      <footer className="text-xs opacity-60 text-center">
        Prototype for Orchids SWE Internship · Built with Next.js & FastAPI
      </footer>
    </div>
  );
}
