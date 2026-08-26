import React, { useState } from "react";
import AuditMark from "./AuditMark.jsx";
import { formatUSD } from "./StatementTotal.jsx";

function LedgerRow({ sub }) {
  const [open, setOpen] = useState(false);

  return (
    <li className="ledger-row">
      <button
        className="ledger-row__main"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <span className="ledger-row__name">{sub.merchant}</span>
        <span className="ledger-row__leader" aria-hidden="true" />
        <span className="ledger-row__price-wrap">
          {sub.price_increased && <AuditMark />}
          <span className="ledger-row__price">{formatUSD(sub.current_amount)}/mo</span>
        </span>
      </button>

      {open && (
        <div className="ledger-row__detail">
          <div className="ledger-row__meta">
            <span>{sub.category}</span>
            <span>&middot;</span>
            <span>{sub.billing_period}</span>
            <span>&middot;</span>
            <span>first seen {sub.first_charge_date}</span>
            <span>&middot;</span>
            <span>{Math.round(sub.confidence * 100)}% confidence</span>
          </div>
          {sub.price_change_events.length > 0 && (
            <div className="ledger-row__history">
              <span className="ledger-row__history-label">Price history</span>
              <ul>
                {sub.price_change_events.map((event, i) => (
                  <li key={i}>
                    {event.date}: {formatUSD(event.old_amount)} &rarr; {formatUSD(event.new_amount)}{" "}
                    <span className={event.pct_change > 0 ? "delta delta--up" : "delta delta--down"}>
                      ({event.pct_change > 0 ? "+" : ""}
                      {event.pct_change}%)
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="ledger-row__annual">Annualized: {formatUSD(sub.estimated_annual_cost)}/yr</div>
        </div>
      )}
    </li>
  );
}

export default function LedgerList({ subscriptions }) {
  return (
    <div className="ledger">
      <div className="ledger__heading">
        <span>Merchant</span>
        <span>Charged</span>
      </div>
      <ul className="ledger__rows">
        {subscriptions.map((sub) => (
          <LedgerRow key={sub.merchant} sub={sub} />
        ))}
      </ul>
    </div>
  );
}
