function showToast(message, type = "success") {
  let toastContainer = document.getElementById("toastContainer");
  
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toastContainer";
    toastContainer.style.position = "fixed";
    toastContainer.style.top = "20px";          // top of screen
    toastContainer.style.left = "50%";          // horizontally center
    toastContainer.style.transform = "translateX(-50%)";
    toastContainer.style.zIndex = 9999;
    toastContainer.style.display = "flex";
    toastContainer.style.flexDirection = "column";
    toastContainer.style.gap = "10px";
    toastContainer.style.pointerEvents = "none"; // clicks pass through
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement("div");
  toast.textContent = message;
  toast.className = `toast ${type}`;
  toast.style.pointerEvents = "all"; // allow hover if needed
  toastContainer.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => {
    toast.style.opacity = "1";
    toast.style.transform = "translateY(0)";
  });

  // Remove after 3 seconds
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(-20px)";
    setTimeout(() => toast.remove(), 400);
  }, 3000);
}

// Creates the toast container if it doesn't exist
function createToastContainer() {
  const container = document.createElement("div");
  container.id = "toastContainer";
  container.style.position = "fixed";
  container.style.top = "20px";
  container.style.right = "20px";
  container.style.zIndex = "10000";
  container.style.display = "flex";
  container.style.flexDirection = "column";
  container.style.gap = "10px";
  document.body.appendChild(container);
  return container;
}

// ----------------- Table Utilities -----------------
function clearTable() {
  const tbody = document.querySelector("#expenseTable tbody");
  tbody.innerHTML = "";
}

function populateTable(expenses) {
  const tbody = document.querySelector("#expenseTable tbody");
  clearTable();

  expenses.forEach(exp => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${exp.date}</td>
      <td>${exp.category}</td>
      <td>$${parseFloat(exp.amount).toFixed(2)}</td>
      <td>${exp.description || ""}</td>
      <td>
        <button class="editBtn" data-id="${exp.id}">Edit</button>
        <button class="deleteBtn" data-id="${exp.id}">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ----------------- Fetch & Chart Data -----------------
async function fetchExpenses() {
  try {
    const res = await fetch("/get_expenses");
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } 
    catch { console.error("Invalid JSON from /get_expenses:", text); return; }

    data.expenses = Array.isArray(data.expenses) ? data.expenses : [];
    data.category = Array.isArray(data.category) ? data.category : [];
    data.monthly = Array.isArray(data.monthly) ? data.monthly : [];

    populateTable(data.expenses);
    renderCategoryChart(data.category);
    renderMonthlyChart(data.monthly);

  } catch (err) { console.error("Failed to load expenses:", err); }
}

async function fetchChartData() {
  try {
    const res = await fetch("/chart_data");
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } 
    catch { console.error("Invalid JSON from /chart_data:", text); return; }

    data.category = Array.isArray(data.category) ? data.category : [];
    data.monthly = Array.isArray(data.monthly) ? data.monthly : [];

    renderCategoryChart(data.category);
    renderMonthlyChart(data.monthly);

  } catch (err) { console.error("Failed to load chart data:", err); }
}

// ----------------- Chart Rendering -----------------
function renderCategoryChart(data) {
  if (!Array.isArray(data) || data.length === 0) {
    Plotly.purge("categoryChart");
    return;
  }
  const validData = data.filter(item => item.category && !isNaN(parseFloat(item.amount)));
  if (!validData.length) { Plotly.purge("categoryChart"); return; }

  Plotly.newPlot("categoryChart", [{
    x: validData.map(d => d.category),
    y: validData.map(d => parseFloat(d.amount)),
    type: "bar",
    marker: { color: "#2b3a67" }
  }], { plot_bgcolor:"#fff", paper_bgcolor:"#fff", xaxis:{title:"Category"}, yaxis:{title:"Amount ($)"}}, { responsive:true });
}

function renderMonthlyChart(data) {
  if (!Array.isArray(data) || data.length === 0) {
    Plotly.purge("monthlyChart");
    return;
  }
  const validData = data.filter(item => item.month && !isNaN(parseFloat(item.amount)));
  if (!validData.length) { Plotly.purge("monthlyChart"); return; }

  Plotly.newPlot("monthlyChart", [{
    x: validData.map(d => d.month),
    y: validData.map(d => parseFloat(d.amount)),
    type: "scatter",
    mode: "lines+markers",
    line: { color: "#ff6b6b" }
  }], { plot_bgcolor:"#fff", paper_bgcolor:"#fff", xaxis:{title:"Month"}, yaxis:{title:"Amount ($)"}}, { responsive:true });
}

// ----------------- ADD EXPENSE -----------------
async function handleAddExpense(e) {
  e.preventDefault();
  const form = e.target;
  const formData = {
    date: form.date.value,
    category: form.category.value,
    amount: form.amount.value,
    description: form.description.value
  };

  try {
    const res = await fetch("/add_expense", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": window.csrfToken },
      body: JSON.stringify(formData)
    });
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch { showToast("Server returned invalid data", "error"); return; }

    data.expenses = Array.isArray(data.expenses) ? data.expenses : [];
    data.category = Array.isArray(data.category) ? data.category : [];
    data.monthly = Array.isArray(data.monthly) ? data.monthly : [];

    if (data.success) {
      populateTable(data.expenses);
      renderCategoryChart(data.category);
      renderMonthlyChart(data.monthly);
      showToast("Expense added!", "success");
      form.reset();
    } else {
      showToast(data.message || "Failed to add expense", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("Failed to add expense", "error");
  }
}
async function handleEditExpense(expId, updatedData) {
  try {
    const res = await fetch(`/edit_expense/${expId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": window.csrfToken },
      body: JSON.stringify(updatedData)
    });
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch { showToast("Server returned invalid data", "error"); return; }

    data.expenses = Array.isArray(data.expenses) ? data.expenses : [];
    data.category = Array.isArray(data.category) ? data.category : [];
    data.monthly = Array.isArray(data.monthly) ? data.monthly : [];

    if (data.success) {
      populateTable(data.expenses);
      renderCategoryChart(data.category);
      renderMonthlyChart(data.monthly);
      showToast("Expense updated!", "success");

      // Highlight the edited row
      const tr = document.querySelector(`button[data-id="${expId}"]`)?.closest("tr");
      if (tr) {
        tr.classList.add("highlight");
        tr.scrollIntoView({ behavior: "smooth", block: "center" });
        setTimeout(() => tr.classList.remove("highlight"), 1200);
      }
    } else {
      showToast(data.message || "Failed to update expense", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("Failed to edit expense", "error");
  }
}

async function handleDeleteExpense(expId) {
  try {
    // Fade out row immediately
    const tr = document.querySelector(`button[data-id="${expId}"]`)?.closest("tr");
    if (tr) tr.classList.add("fade-out");

    const res = await fetch(`/delete_expense/${expId}`, {
      method: "POST",
      headers: { "X-CSRFToken": window.csrfToken }
    });
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch { showToast("Server returned invalid data", "error"); return; }

    data.expenses = Array.isArray(data.expenses) ? data.expenses : [];
    data.category = Array.isArray(data.category) ? data.category : [];
    data.monthly = Array.isArray(data.monthly) ? data.monthly : [];

    if (data.success) {
      populateTable(data.expenses);
      renderCategoryChart(data.category);
      renderMonthlyChart(data.monthly);
      showToast("Expense deleted!", "success");
    } else {
      showToast(data.message || "Failed to delete expense", "error");
    }
  } catch (err) {
    console.error(err);
    showToast("Failed to delete expense", "error");
  }
}

// ----------------- Event Listeners -----------------
document.addEventListener("DOMContentLoaded", () => {
  fetchExpenses();

  const expenseForm = document.getElementById("expenseForm");
  expenseForm.addEventListener("submit", handleAddExpense);

  // Table button delegation
  document.querySelector("#expenseTable tbody").addEventListener("click", (e) => {
    const target = e.target;
    const expId = target.dataset.id;
    if (target.classList.contains("editBtn")) {
      const tr = target.closest("tr");
      openEditModal(expId, {
        date: tr.children[0].textContent,
        category: tr.children[1].textContent,
        amount: parseFloat(tr.children[2].textContent.replace("$", "")),
        description: tr.children[3].textContent
      });
    }
    if (target.classList.contains("deleteBtn")) {
      openDeleteModal(expId);
    }
  });

  const editModal = document.getElementById("editModal");
  const editForm = document.getElementById("editExpenseForm");
  const editCancel = document.getElementById("editCancel");
  const editModalContent = editModal.querySelector(".edit-modal-content");
  
  function openEditModal(expId, data) {
    editForm.date.value = data.date;
    editForm.category.value = data.category;
    editForm.amount.value = data.amount;
    editForm.description.value = data.description || "";
    editModal.classList.add("active");
  
    editForm.onsubmit = async (e) => {
      e.preventDefault();
      await handleEditExpense(expId, {
        date: editForm.date.value,
        category: editForm.category.value,
        amount: editForm.amount.value,
        description: editForm.description.value
      });
      editModal.classList.remove("active");
    };
  }
  
  // Close modal when clicking cancel button
  editCancel.addEventListener("click", () => editModal.classList.remove("active"));
  
  // Close modal when clicking outside the content
  editModal.addEventListener("click", (e) => {
    if (!editModalContent.contains(e.target)) {
      editModal.classList.remove("active");
    }
  });
  
  // ----------------- Delete Modal -----------------
  const deleteModal = document.getElementById("deleteModal");
  const deleteConfirm = document.getElementById("deleteConfirm");
  const deleteCancel = document.getElementById("deleteCancel");
  const deleteModalContent = deleteModal.querySelector(".delete-modal-content");
  
  let expenseToDelete = null;
  
  function openDeleteModal(expId) {
    expenseToDelete = expId;
    deleteModal.classList.add("active");
  }
  
  // Cancel delete
  deleteCancel.addEventListener("click", () => {
    expenseToDelete = null;
    deleteModal.classList.remove("active");
  });
  
  // Confirm delete
  deleteConfirm.addEventListener("click", async () => {
    if (!expenseToDelete) return;
    await handleDeleteExpense(expenseToDelete);
    expenseToDelete = null;
    deleteModal.classList.remove("active");
  });
  
  // Close modal when clicking outside the content
  deleteModal.addEventListener("click", (e) => {
    if (!deleteModalContent.contains(e.target)) {
      expenseToDelete = null;
      deleteModal.classList.remove("active");
    }
  });
});