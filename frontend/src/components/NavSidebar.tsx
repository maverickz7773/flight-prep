"use client";

import { useState, useEffect } from "react";

const SECTIONS = [
  { id: "section-1", num: 1, label: "Overview" },
  { id: "section-2", num: 2, label: "Fuel" },
  { id: "section-3", num: 3, label: "Weights" },
  { id: "section-4", num: 4, label: "Takeoff" },
  { id: "section-5", num: 5, label: "Route" },
  { id: "section-6", num: 6, label: "Arrival" },
  { id: "section-7", num: 7, label: "Wx & NOTAM" },
  { id: "section-8", num: 8, label: "Insights" },
  { id: "section-9", num: 9, label: "Solat" },
];

export default function NavSidebar() {
  const [activeId, setActiveId] = useState("");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        }
      },
      { rootMargin: "-10% 0px -80% 0px" },
    );

    for (const s of SECTIONS) {
      const el = document.getElementById(s.id);
      if (el) observer.observe(el);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <>
      {/* Desktop sidebar */}
      <nav className="fixed left-2 top-1/2 -translate-y-1/2 z-50 no-print hidden xl:flex flex-col gap-1 bg-surface/90 backdrop-blur border border-border rounded-lg p-1.5 shadow-lg">
        {SECTIONS.map((s) => (
          <a
            key={s.id}
            href={`#${s.id}`}
            title={s.label}
            className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors whitespace-nowrap ${
              activeId === s.id
                ? "bg-accent-green/20 text-accent-green font-bold"
                : "text-muted hover:text-foreground hover:bg-surface-2"
            }`}
          >
            <span className="w-4 text-right tabular-nums">{s.num}.</span>
            <span>{s.label}</span>
          </a>
        ))}
      </nav>

      {/* Mobile bottom bar */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 no-print xl:hidden bg-surface/95 backdrop-blur border-t border-border shadow-lg">
        <div className="flex overflow-x-auto gap-1 px-2 py-1.5 scrollbar-hide">
          {SECTIONS.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className={`flex-shrink-0 px-3 py-1.5 rounded-full text-xs transition-colors whitespace-nowrap ${
                activeId === s.id
                  ? "bg-accent-green/20 text-accent-green font-bold"
                  : "text-muted hover:text-foreground"
              }`}
            >
              {s.num}. {s.label}
            </a>
          ))}
        </div>
      </nav>
    </>
  );
}
