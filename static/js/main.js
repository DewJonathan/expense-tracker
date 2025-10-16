document.addEventListener("DOMContentLoaded", async () => {
    try {
        const res = await fetch("/chart_data");
        const data = await res.json();

        // CATEGORY CHART
        if (data.category.length > 0) {
            const catDiv = document.getElementById("category-chart");
            const catLabels = data.category.map(d => d.category);
            const catAmounts = data.category.map(d => d.amount);

            const catTrace = {
                x: catLabels,
                y: catAmounts,
                type: "bar",
                text: catAmounts.map(a => `$${a.toFixed(2)}`),
                textposition: "auto",
                marker: { color: "#3B82F6" }
            };

            Plotly.newPlot(catDiv, [catTrace], {
                title: "Spending by Category",
                xaxis: { title: "Category" },
                yaxis: { title: "Amount ($)" }
            });
        }

        // MONTHLY CHART
        if (data.monthly.length > 0) {
            const monDiv = document.getElementById("monthly-chart");
            const months = data.monthly.map(d => d.month);
            const amounts = data.monthly.map(d => d.amount);

            const monTrace = {
                x: months,
                y: amounts,
                type: "scatter",
                mode: "lines+markers",
                line: { color: "#10B981" }
            };

            Plotly.newPlot(monDiv, [monTrace], {
                title: "Monthly Spending Trend",
                xaxis: { title: "Month" },
                yaxis: { title: "Amount ($)" }
            });
        }
    } catch (err) {
        console.error("Error loading charts:", err);
    }
});