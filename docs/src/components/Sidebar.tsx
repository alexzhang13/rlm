"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { ChevronDown } from "lucide-react";
import { useState } from "react";

const navigation = [
  { name: "Recursive Language Models", href: "/" },
  { name: "Using the RLM Client", href: "/api" },
  { name: "LM Backends", href: "/backends" },
  {
    name: "REPL Environments",
    children: [
      { name: "Overview", href: "/environments" },
      { name: "LocalREPL", href: "/environments/local" },
      { name: "DockerREPL", href: "/environments/docker" },
      { name: "ModalREPL", href: "/environments/modal" },
    ],
  },
  { name: "Visualizing RLM Trajectories", href: "/trajectories" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [expandedSections, setExpandedSections] = useState<string[]>(["REPL Environments"]);

  const toggleSection = (name: string) => {
    setExpandedSections((prev) =>
      prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
    );
  };

  return (
    <aside className="w-64 border-r border-border bg-card/50 backdrop-blur-sm min-h-screen sticky top-0">
      <div className="p-6 border-b border-border">
        <Link href="/" className="block">
          <h1 className="font-bold text-xl text-foreground tracking-tight">
            RLM
          </h1>
        </Link>
      </div>
      <nav className="px-4 pb-8 pt-4">
        <ul className="space-y-0.5">
          {navigation.map((item) => {
            if ("children" in item) {
              const isExpanded = expandedSections.includes(item.name);
              return (
                <li key={item.name}>
                  <button
                    onClick={() => toggleSection(item.name)}
                    className="flex items-center justify-between w-full px-3 py-2 text-sm font-medium text-muted-foreground hover:text-foreground rounded-md hover:bg-accent transition-colors"
                  >
                    {item.name}
                    <ChevronDown
                      className={cn(
                        "h-4 w-4 transition-transform",
                        isExpanded && "rotate-180"
                      )}
                    />
                  </button>
                  {isExpanded && item.children && (
                    <ul className="mt-1 ml-3 space-y-1 border-l border-border pl-3">
                      {item.children.map((child) => (
                        <li key={child.href}>
                          <Link
                            href={child.href}
                            className={cn(
                              "block px-3 py-1.5 text-sm rounded-md transition-colors",
                              pathname === child.href
                                ? "text-foreground font-semibold bg-accent"
                                : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                            )}
                          >
                            {child.name}
                          </Link>
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              );
            }
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "block px-3 py-2 text-sm rounded-md transition-colors",
                    pathname === item.href
                      ? "text-foreground font-semibold bg-accent"
                      : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                  )}
                >
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="absolute bottom-4 left-4 right-4">
        <a
          href="https://github.com/Delta-Labs-AG/rlm"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:text-foreground rounded-md hover:bg-accent"
        >
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
          </svg>
          GitHub
        </a>
      </div>
    </aside>
  );
}

