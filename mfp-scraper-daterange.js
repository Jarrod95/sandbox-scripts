(async function () {
  // --------- CONFIG ---------
  // The diary page usually works like /food/diary?date=YYYY-MM-DD
  const DIARY_URL = (isoDate) => `/food/diary?date=${isoDate}`;

  // Throttle so you don't hammer the site (ms between requests)
  const REQUEST_DELAY_MS = 400;

  // --------- HELPERS ---------
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function toISODate(d) {
    // local date -> YYYY-MM-DD
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  }

  function toAUDate(d) {
    // DD/MM/YYYY
    const dd = String(d.getDate()).padStart(2, "0");
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const yyyy = d.getFullYear();
    return `${dd}/${mm}/${yyyy}`;
  }

  function parseDiaryFromDocument(doc, diaryDateAU) {
    // Try a couple of known layouts/selectors.
    // Your current one:
    const rows = doc.querySelectorAll("#diary-table tbody tr");

    if (!rows || rows.length === 0) {
      // If MFP changes layout, this will fail. We'll throw a helpful message.
      throw new Error(
        "Couldn't find #diary-table rows on this diary page. MFP may have changed the layout for your account."
      );
    }

    const data = [];
    let currentMeal = "";

    rows.forEach((row) => {
      if (row.classList.contains("meal_header")) {
        currentMeal = row.innerText.trim();
      } else if (row.querySelector("td") && !row.classList.contains("bottom")) {
        const food = row.querySelector("td:nth-child(1)")?.innerText.trim() || "";
        if (["Totals", "Your Daily Goal", "Remaining"].includes(food)) return;

        const calories = row.querySelector("td:nth-child(2)")?.innerText.trim() || "";
        const carbs = row.querySelector("td:nth-child(3)")?.innerText.trim() || "";
        const fat = row.querySelector("td:nth-child(4)")?.innerText.trim() || "";
        const protein = row.querySelector("td:nth-child(5)")?.innerText.trim() || "";
        const sodium = row.querySelector("td:nth-child(6)")?.innerText.trim() || "";
        const sugar = row.querySelector("td:nth-child(7)")?.innerText.trim() || "";

        data.push([diaryDateAU, currentMeal, food, calories, carbs, fat, protein, sodium, sugar]);
      }
    });

    return data;
  }

  function buildCSV(headers, rows) {
    const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
    return headers.map(esc).join(",") + "\n" + rows.map((r) => r.map(esc).join(",")).join("\n");
  }

  // --------- INPUTS ---------
  const startStr = prompt("Start date (YYYY-MM-DD):", "2026-02-01");
  const endStr = prompt("End date (YYYY-MM-DD):", "2026-02-10");

  const start = new Date(startStr + "T00:00:00");
  const end = new Date(endStr + "T00:00:00");

  if (isNaN(start) || isNaN(end) || start > end) {
    console.error("Invalid date range.");
    return;
  }

  // --------- MAIN ---------
  const headers = ["Date", "Meal", "Food", "Calories", "Carbs", "Fat", "Protein", "Sodium", "Sugar"];
  const allRows = [];

  // Walk inclusive range
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    const iso = toISODate(d);
    const au = toAUDate(d);

    const url = DIARY_URL(iso);

    console.log(`Fetching ${iso} -> ${url}`);
    const res = await fetch(url, {
      method: "GET",
      credentials: "include",
      headers: {
        "Accept": "text/html",
      },
    });

    if (!res.ok) {
      console.warn(`Skipping ${iso}: HTTP ${res.status}`);
      await sleep(REQUEST_DELAY_MS);
      continue;
    }

    const html = await res.text();
    const doc = new DOMParser().parseFromString(html, "text/html");

    try {
      const dayRows = parseDiaryFromDocument(doc, au);
      console.log(`  ${iso}: ${dayRows.length} rows`);
      allRows.push(...dayRows);
    } catch (e) {
      console.warn(`  ${iso}: parse failed -> ${e.message}`);
    }

    await sleep(REQUEST_DELAY_MS);
  }

  if (allRows.length === 0) {
    console.error("No rows collected. Likely layout/selector mismatch.");
    return;
  }

  const csv = buildCSV(headers, allRows);
  const filename = `${toISODate(start)}_to_${toISODate(end)}-mfp.csv`;
  downloadCSV(csv, filename);
  console.log(`Done. Downloaded ${filename} with ${allRows.length} rows.`);
})();
