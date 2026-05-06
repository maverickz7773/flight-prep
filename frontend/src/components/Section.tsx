"use client";

import { useState } from "react";

export default function Section({
  number,
  title,
  children,
  defaultOpen = true,
}: {
  number: number;
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div
      id={`section-${number}`}
      className="bg-surface border border-border rounded-lg overflow-hidden scroll-mt-24 sm:scroll-mt-28 xl:scroll-mt-4"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-surface-2 transition-colors no-print-collapse"
      >
        <span className="text-accent-green text-xs font-bold w-5">
          {number}.
        </span>
        <span className="text-foreground font-bold text-sm flex-1">
          {title}
        </span>
        <span className="text-muted text-xs no-print">{open ? "▼" : "▶"}</span>
      </button>
      {open && (
        <div className="px-4 pb-3 text-sm leading-relaxed">{children}</div>
      )}
    </div>
  );
}
