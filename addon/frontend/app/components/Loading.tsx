import React from "react";

export default function Loading() {
  return (
    <div className="flex h-screen w-full items-center justify-center">
      <div role="status" aria-live="polite" aria-busy="true" className="text-zinc-700 dark:text-zinc-200">
        <svg
          className="size-10 animate-spin motion-reduce:animate-none"
          viewBox="0 0 50 50"
          aria-hidden="true"
        >
          <circle
            className="ha-spinner-circle stroke-current"
            cx="25"
            cy="25"
            r="20"
            fill="none"
            strokeWidth="3"
            strokeLinecap="round"
          />
        </svg>
        <span className="sr-only">Loading</span>
      </div>
      <style>
        {`
        @keyframes ha-spinner-dash {
          0% {
            stroke-dasharray: 1, 200;
            stroke-dashoffset: 0;
          }
          50% {
            stroke-dasharray: 90, 200;
            stroke-dashoffset: -35px;
          }
          100% {
            stroke-dasharray: 90, 200;
            stroke-dashoffset: -124px;
          }
        }

        .ha-spinner-circle {
          stroke-dasharray: 1, 200;
          stroke-dashoffset: 0;
          animation: ha-spinner-dash 1.5s ease-in-out infinite;
        }

        @media (prefers-reduced-motion: reduce) {
          .ha-spinner-circle {
            animation: none !important;
          }
        }
        `}
      </style>
    </div>
  );
}




