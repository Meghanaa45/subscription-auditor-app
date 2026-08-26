import React from "react";

function formatUSD(value) {
  return `$${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function StatementTotal({ summary }) {
  return (
    <div className="statement-total">
      <div className="statement-total__row">
        <span className="statement-total__label">Statement total</span>
        <span className="statement-total__rule" aria-hidden="true" />
      </div>
      <div className="statement-total__figures">
        <div className="figure">
          <span className="figure__value">{formatUSD(summary.total_monthly_cost)}</span>
          <span className="figure__label">per month</span>
        </div>
        <div className="figure">
          <span className="figure__value">{formatUSD(summary.total_annual_cost)}</span>
          <span className="figure__label">per year</span>
        </div>
        <div className="figure">
          <span className="figure__value">{summary.total_subscriptions}</span>
          <span className="figure__label">subscriptions found</span>
        </div>
        <div className="figure figure--flag">
          <span className="figure__value">{summary.subscriptions_with_price_increases}</span>
          <span className="figure__label">flagged for price increases</span>
        </div>
      </div>
    </div>
  );
}

export { formatUSD };
