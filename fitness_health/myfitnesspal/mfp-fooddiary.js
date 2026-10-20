
(async () => {
  "use strict";

  const CONFIG = {
    start: "2026-04-01",
    end: "2026-10-20",
    concurrency: 3,
    delayMs: 500,
    retries: 3,
    prefix: "mfp_2026_apr_oct"
  };

  // Browsers cannot silently write to a Windows path. A real click is required
  // to grant access to the repository's myfitnesspal/data directory.
  async function selectOutputDirectory() {
    if (!window.showDirectoryPicker) {
      console.warn("Folder writing unavailable; falling back to Downloads.");
      return null;
    }
    return new Promise(resolve => {
      const button = document.createElement("button");
      button.textContent = "Choose sandbox-scripts/fitness_health/myfitnesspal/data for MFP export";
      Object.assign(button.style, {
        position:"fixed", top:"16px", right:"16px", zIndex:"2147483647",
        padding:"12px", color:"#fff", background:"#145a92",
        border:"2px solid #fff", borderRadius:"8px", cursor:"pointer"
      });
      document.body.appendChild(button);
      console.log("Click the blue button and choose your local sandbox-scripts/fitness_health/myfitnesspal/data folder.");
      button.addEventListener("click", async () => {
        try {
          // Picker call must be directly associated with a user gesture.
          const handle = await window.showDirectoryPicker({mode:"readwrite", id:"mfp-data"});
          if (handle.name !== "data") {
            const proceed = window.confirm(
              "Selected folder is '" + handle.name + "', not 'data'. Use it anyway?"
            );
            if (!proceed) return;
          }
          button.remove();
          resolve(handle);
        } catch (error) {
          if (error.name === "AbortError") {
            console.warn("Directory selection cancelled. Click again to choose a folder.");
          } else {
            console.warn("Folder access failed; using Downloads.", error);
            button.remove();
            resolve(null);
          }
        }
      });
    });
  }

  function downloadFallback(content, filename, type) {
    const blob = new Blob([content], {type});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  }

  async function saveExport(folder, content, filename, type) {
    if (!folder) {
      downloadFallback(content, filename, type);
      return;
    }
    const handle = await folder.getFileHandle(filename, {create:true});
    const writable = await handle.createWritable();
    try {
      await writable.write(content);
      await writable.close();
      console.log("Saved to chosen folder:", filename);
    } catch (error) {
      try { await writable.abort(); } catch {}
      throw error;
    }
  }

  const outputFolder = await selectOutputDirectory();

  const sleep = ms => new Promise(r => setTimeout(r, ms));

  const number = value => {
    const n = Number(
      String(value ?? "").replace(/,/g, "").trim()
    );
    return Number.isFinite(n) ? n : null;
  };

  const dates = [];
  for (
    let d = new Date(CONFIG.start + "T12:00:00");
    d <= new Date(CONFIG.end + "T12:00:00");
    d.setDate(d.getDate() + 1)
  ) {
    dates.push([
      d.getFullYear(),
      String(d.getMonth() + 1).padStart(2, "0"),
      String(d.getDate()).padStart(2, "0")
    ].join("-"));
  }

  const nutrients = [
    "calories", "carbs_g", "fat_g",
    "protein_g", "sodium_mg", "sugar_g"
  ];

  function readNutrients(cells) {
    const result = {};

    nutrients.forEach((name, i) => {
      const cell = cells[i + 1];
      if (!cell) {
        result[name] = null;
        return;
      }

      // Macro cells contain BOTH grams and percentages.
      // Only use .macro-value, never .macro-percentage.
      const macro = cell.querySelector(".macro-value");

      result[name] = number(
        macro
          ? macro.textContent
          : cell.textContent
      );
    });

    return result;
  }

  function parsePage(html, date) {
    const doc = new DOMParser().parseFromString(
      html, "text/html"
    );

    const table = doc.querySelector("#diary-table");

    if (!table) {
      throw new Error(
        "Missing #diary-table; possible login redirect"
      );
    }

    const foods = [];
    const meals = [];
    let currentMeal = null;
    let dailyTotals = null;
    let dailyGoal = null;
    let remaining = null;

    for (const tr of table.querySelectorAll("tr")) {
      const cells = [...tr.children].filter(
        el => el.tagName === "TD"
      );

      if (!cells.length) continue;

      const classes = tr.classList;

      if (classes.contains("meal_header")) {
        currentMeal = cells[0].textContent.trim();
        continue;
      }

      if (classes.contains("bottom")) {
        if (currentMeal) {
          meals.push({
            date,
            meal: currentMeal,
            ...readNutrients(cells)
          });
        }
        continue;
      }

      if (classes.contains("total")) {
        const label = cells[0].textContent.trim();
        const values = readNutrients(cells);

        if (label === "Totals") {
          dailyTotals = values;
        } else if (label === "Your Daily Goal") {
          dailyGoal = values;
        } else if (label === "Remaining") {
          remaining = values;
        }
        continue;
      }

      if (classes.contains("spacer")) continue;
      if (!currentMeal || cells.length < 7) continue;

      const foodLink = cells[0].querySelector(
        "a.js-show-edit-food"
      );

      // Actual food rows have this link.
      // This excludes action buttons, headers and footers.
      if (!foodLink) continue;

      const food = foodLink.textContent
        .replace(/\s+/g, " ")
        .trim();

      foods.push({
        date,
        meal: currentMeal,
        food,
        entry_id:
          foodLink.dataset.foodEntryId || "",
        ...readNutrients(cells)
      });
    }

    if (!dailyTotals) {
      throw new Error("Daily Totals row missing");
    }

    const summedCalories = foods.reduce(
      (sum, f) => sum + (f.calories || 0), 0
    );

    const difference =
      summedCalories - dailyTotals.calories;

    return {
      date,
      foods,
      meals,
      daily: {
        date,
        ...dailyTotals,
        goal_calories: dailyGoal?.calories ?? null,
        remaining_calories:
          remaining?.calories ?? null,
        food_entries: foods.length,
        summed_food_calories: summedCalories,
        calorie_difference: difference,
        validated: Math.abs(difference) <= 1
      }
    };
  }

  // Check the CURRENT page before crawling anything.
  const today = new URLSearchParams(
    location.search
  ).get("date") || CONFIG.end;

  const test = parsePage(
    document.documentElement.outerHTML,
    today
  );

  console.log("CURRENT PAGE VALIDATION");
  console.table(test.foods.slice(0, 10));
  console.table([test.daily]);

  if (!test.daily.validated) {
    console.warn(
      "Current page calorie totals do not match.",
      test.daily
    );
  }

  const base = location.origin + "/food/diary";
  const results = new Array(dates.length);
  const errors = [];

  let next = 0;
  let completed = 0;
  let stopped = false;

  // Stop manually with: window.mfpStop = true
  window.mfpStop = false;

  async function fetchDay(date) {
    const url = `${base}?date=${date}`;

    for (let attempt = 1; attempt <= CONFIG.retries; attempt++) {
      try {
        const response = await fetch(url, {
          credentials: "include",
          headers: { Accept: "text/html" }
        });

        if (
          response.status === 401 ||
          response.status === 403
        ) {
          throw new Error(
            `Access denied: HTTP ${response.status}`
          );
        }

        if (response.status === 429) {
          throw new Error("Rate limited: HTTP 429");
        }

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const html = await response.text();
        const parsed = parsePage(html, date);

        // Ensure server actually returned the requested day.
        const selectedDate = html.match(
          /MFP\.Food\.Note\.init\(['"](\d{4}-\d{2}-\d{2})/
        )?.[1];

        if (selectedDate && selectedDate !== date) {
          throw new Error(
            `Date mismatch: requested ${date}, got ${selectedDate}`
          );
        }

        return parsed;

      } catch (error) {
        if (
          /Access denied|Rate limited/.test(error.message)
        ) {
          stopped = true;
          window.mfpStop = true;
          throw error;
        }

        if (attempt === CONFIG.retries) throw error;

        await sleep(1000 * attempt);
      }
    }
  }

  async function worker() {
    while (!window.mfpStop) {
      const i = next++;
      if (i >= dates.length) return;

      const date = dates[i];

      try {
        results[i] = await fetchDay(date);
      } catch (error) {
        errors.push({
          date,
          error: error.message
        });
      }

      completed++;

      if (completed % 5 === 0 || completed === dates.length) {
        const pct = (
          completed / dates.length * 100
        ).toFixed(1);

        console.log(
          `${pct}% | ${completed}/${dates.length} days | ` +
          `${errors.length} errors`
        );
      }

      await sleep(CONFIG.delayMs);
    }
  }

  console.log(`Starting crawl: ${dates.length} days`);

  await Promise.all(
    Array.from(
      { length: CONFIG.concurrency },
      () => worker()
    )
  );

  const successful = results.filter(Boolean);
  const foods = successful.flatMap(r => r.foods);
  const meals = successful.flatMap(r => r.meals);
  const daily = successful.map(r => r.daily);

  function csvEscape(value) {
    if (value == null) return "";
    const str = String(value);
    return `"${str.replace(/"/g, '""')}"`;
  }

  function toCSV(rows, fields) {
    return [
      fields.join(","),
      ...rows.map(row =>
        fields.map(f => csvEscape(row[f])).join(",")
      )
    ].join("\r\n");
  }

  const foodFields = [
    "date", "meal", "food", "entry_id",
    ...nutrients
  ];

  const mealFields = [
    "date", "meal", ...nutrients
  ];

  const dailyFields = [
    "date", ...nutrients,
    "goal_calories", "remaining_calories",
    "food_entries", "summed_food_calories",
    "calorie_difference", "validated"
  ];

  await saveExport(
    outputFolder,
    toCSV(foods, foodFields),
    CONFIG.prefix + "_foods.csv",
    "text/csv"
  );

  await saveExport(
    outputFolder,
    toCSV(meals, mealFields),
    CONFIG.prefix + "_meals.csv",
    "text/csv"
  );

  await saveExport(
    outputFolder,
    toCSV(daily, dailyFields),
    CONFIG.prefix + "_daily.csv",
    "text/csv"
  );

  await saveExport(
    outputFolder,
    JSON.stringify({
      config: CONFIG,
      successful_days: successful.length,
      requested_days: dates.length,
      errors,
      results: successful
    }, null, 2),
    CONFIG.prefix + "_full.json",
    "application/json"
  );

  window.mfpExport = {
    foods, meals, daily, errors, results: successful
  };

  console.log("EXTRACTION COMPLETE");

  console.table({
    requested_days: dates.length,
    successful_days: successful.length,
    food_entries: foods.length,
    meal_summaries: meals.length,
    errors: errors.length,
    calorie_mismatches:
      daily.filter(d => !d.validated).length
  });

  console.table(daily.slice(-10));

  if (errors.length) console.table(errors);

  if (stopped) {
    console.warn(
      "Crawl stopped after an access/rate-limit response."
    );
  }
})();
