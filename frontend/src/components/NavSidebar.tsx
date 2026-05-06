"use client";

import { useState, useEffect, useRef } from "react";

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
  const mobileTabRefs = useRef<Record<string, HTMLAnchorElement | null>>({});

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

  useEffect(() => {
    if (!activeId) return;
    mobileTabRefs.current[activeId]?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
      inline: "center",
    });
  }, [activeId]);

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

      {/* Mobile top tabs */}
      <nav className="sticky top-0 z-40 no-print xl:hidden -mx-2 sm:-mx-4 mb-3 border-y border-border bg-background/95 backdrop-blur shadow-sm">
        <div className="mobile-tab-scroll flex overflow-x-auto gap-2 px-2 py-2">
          {SECTIONS.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              ref={(el) => {
                mobileTabRefs.current[s.id] = el;
              }}
              className={`flex-shrink-0 rounded-full px-4 py-2 text-sm leading-none transition-colors whitespace-nowrap ${
                activeId === s.id
                  ? "bg-accent-green/20 text-accent-green font-bold shadow-[inset_0_0_0_1px_rgba(0,255,136,0.18)]"
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
