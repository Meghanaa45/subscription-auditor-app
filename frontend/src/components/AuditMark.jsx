import React from "react";

/* An intentionally imperfect ellipse, like a pen circle drawn by hand around
   a number on a statement - the signature visual for a flagged price. */
export default function AuditMark() {
  return (
    <svg className="audit-mark" viewBox="0 0 120 56" aria-hidden="true">
      <path
        d="M 14 30 C 10 14, 34 4, 60 5 C 90 6, 112 14, 108 30 C 104 48, 76 52, 58 51 C 30 50, 18 44, 14 30 Z"
        fill="none"
        stroke="var(--audit-red)"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  );
}
