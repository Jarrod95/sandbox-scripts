(function() {
  function downloadCSV(csv, filename) {
    let blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement("a");
    if (link.download !== undefined) {
      let url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute("download", filename);
      link.style.visibility = "hidden";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }

  // Grab diary date text from page
  let diaryDateRaw = document.querySelector("#date")?.innerText.trim() 
                  || document.querySelector(".date")?.innerText.trim()
                  || "";

  // Convert to Date object
  let dateObj = new Date(diaryDateRaw);
  let diaryDate = "";
  if (!isNaN(dateObj)) {
    let dd = String(dateObj.getDate()).padStart(2, '0');
    let mm = String(dateObj.getMonth() + 1).padStart(2, '0'); 
    let yyyy = dateObj.getFullYear();
    diaryDate = `${dd}/${mm}/${yyyy}`;
  } else {
    diaryDate = diaryDateRaw; 
  }

  // Extract diary rows
  let rows = document.querySelectorAll("#diary-table tbody tr");
  let data = [];
  let headers = ["Date", "Meal", "Food", "Calories", "Carbs", "Fat", "Protein", "Sodium", "Sugar"];

  let currentMeal = "";
  rows.forEach(row => {
    if (row.classList.contains("meal_header")) {
      currentMeal = row.innerText.trim();
    } 
    else if (row.querySelector("td") && !row.classList.contains("bottom")) {
      let food = row.querySelector("td:nth-child(1)")?.innerText.trim() || "";
      
      // skip totals/goal/remaining rows
      if (["Totals", "Your Daily Goal", "Remaining"].includes(food)) return;

      let calories = row.querySelector("td:nth-child(2)")?.innerText.trim() || "";
      let carbs = row.querySelector("td:nth-child(3)")?.innerText.trim() || "";
      let fat = row.querySelector("td:nth-child(4)")?.innerText.trim() || "";
      let protein = row.querySelector("td:nth-child(5)")?.innerText.trim() || "";
      let sodium = row.querySelector("td:nth-child(6)")?.innerText.trim() || "";
      let sugar = row.querySelector("td:nth-child(7)")?.innerText.trim() || "";

      data.push([diaryDate, currentMeal, food, calories, carbs, fat, protein, sodium, sugar]);
    }
  });

  // Build CSV
  let csvContent = headers.join(",") + "\n" +
                   data.map(r => r.map(v => `"${v}"`).join(",")).join("\n");

  // Name file as <date>-mfp.csv
  let safeDate = diaryDate.replace(/\//g, "-"); // 21-08-2025
  let filename = `${safeDate}-mfp.csv`;

  downloadCSV(csvContent, filename);
})();
