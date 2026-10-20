
(async () => {
  "use strict";

  const CONFIG = {
    startDate: "2026-04-01",
    endDate: "2026-10-20",
    periods: [365, 180, 90, 30],
    filename: "myfitnesspal_weight_history.csv"
  };

  const records = new Map();
  const diagnostics = [];

  function parseDate(value) {
    const text = String(value || "").trim();

    // Handles YYYY-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
      return text;
    }

    // Handles MM/DD, as seen in your screenshot.
    const match = text.match(/^(\d{1,2})\/(\d{1,2})(?:\/(\d{4}))?$/);

    if (match) {
      const month = Number(match[1]);
      const day = Number(match[2]);
      const year = Number(match[3] || 2026);

      const date = new Date(Date.UTC(year, month - 1, day));

      if (
        date.getUTCFullYear() !== year ||
        date.getUTCMonth() !== month - 1 ||
        date.getUTCDate() !== day
      ) {
        return null;
      }

      return [
        year,
        String(month).padStart(2, "0"),
        String(day).padStart(2, "0")
      ].join("-");
    }

    return null;
  }

  for (const days of CONFIG.periods) {
    const url = `/api/services/reports/results/progress/1/${days}`;

    console.log(`Fetching ${days}-day weight history...`);

    try {
      const response = await fetch(url, {
        method: "GET",
        credentials: "include",
        headers: {
          Accept: "application/json"
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const json = await response.json();
      const rows = json?.outcome?.results;

      if (!Array.isArray(rows)) {
        throw new Error("Unexpected response structure");
      }

      let accepted = 0;

      for (const item of rows) {
        const date = parseDate(item.date);
        const weight = Number(item.total);

        if (!date || !Number.isFinite(weight)) continue;
        if (date < CONFIG.startDate ||
            date > CONFIG.endDate) continue;

        // Assumes chart is configured to show kilograms.
        if (weight < 20 || weight > 400) continue;

        records.set(date, {
          date,
          weight_kg: weight
        });

        accepted++;
      }

      diagnostics.push({
        period: days,
        status: "OK",
        returned: rows.length,
        accepted,
        unique_total: records.size
      });

    } catch (error) {
      diagnostics.push({
        period: days,
        status: error.message,
        returned: 0,
        accepted: 0,
        unique_total: records.size
      });
    }
  }

  const weights = [...records.values()]
    .sort((a, b) => a.date.localeCompare(b.date));

  window.mfpWeightHistory = weights;

  console.log("REQUEST RESULTS");
  console.table(diagnostics);

  console.log("WEIGHT HISTORY");
  console.table(weights);

  if (!weights.length) {
    console.error("No weight measurements extracted.");
    return;
  }

  const csv = [
    "date,weight_kg",
    ...weights.map(r => `${r.date},${r.weight_kg}`)
  ].join("\r\n");

  const blob = new Blob([csv], {
    type: "text/csv;charset=utf-8"
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = CONFIG.filename;

  document.body.appendChild(link);
  link.click();
  link.remove();

  setTimeout(() => URL.revokeObjectURL(url), 5000);

  console.log(
    `Exported ${weights.length} unique measurements`
  );

  console.log(
    `Date range: ${weights[0].date} to ` +
    `${weights[weights.length - 1].date}`
  );
})();
