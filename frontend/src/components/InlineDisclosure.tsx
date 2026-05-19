"use client";

import { useState } from "react";

export default function InlineDisclosure({
  title,
  children,
  defaultOpen = false,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  className?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={className}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full text-left text-accent-green text-xs font-bold hover:text-foreground transition-colors"
      >
        {open ? "▼" : "▶"} {title}
      </button>
      {open && <div className="mt-2">{children}</div>}
    </div>
  );
}
