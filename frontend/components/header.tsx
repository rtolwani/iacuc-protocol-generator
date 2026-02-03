"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

export function Header() {
  return (
    <header className="border-b bg-background">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <svg
            className="h-8 w-8 text-primary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <span className="font-bold text-lg">IACUC Protocol Generator</span>
        </Link>
        
        <nav className="flex items-center gap-4">
          <Link href="/protocols" className="text-muted-foreground hover:text-foreground transition">
            Protocols
          </Link>
          <Link href="/review" className="text-muted-foreground hover:text-foreground transition">
            Review
          </Link>
          <Button asChild>
            <Link href="/protocols/new">New Protocol</Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}
