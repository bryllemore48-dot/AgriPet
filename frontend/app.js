const ordersData = [
  { id: '#ORD-1048', customer: 'Juan Dela Cruz', total: '₱2,450.00', status: 'Completed', date: 'May 25, 2025' },
  { id: '#ORD-1047', customer: 'Maria Santos', total: '₱1,850.00', status: 'Processing', date: 'May 25, 2025' },
  { id: '#ORD-1046', customer: 'Pedro Reyes', total: '₱3,200.00', status: 'Shipped', date: 'May 24, 2025' },
  { id: '#ORD-1045', customer: 'Ava Cruz', total: '₱1,150.00', status: 'Completed', date: 'May 23, 2025' },
];

const lowStockData = [
  { name: 'Cat Litter 10kg', stock: 3, threshold: 10 },
  { name: 'Dog Treats 500g', stock: 2, threshold: 5 },
  { name: 'Bird Seeds 1kg', stock: 1, threshold: 5 },
];

const storesOverview = {
  labels: ['May 19', 'May 20', 'May 21', 'May 22', 'May 23', 'May 24', 'May 25'],
  values: [4200, 6000, 5200, 7000, 6400, 8400, 7600],
};

const categoryData = {
  labels: ['Cat Food', 'Dog Food', 'Accessories', 'Treats', 'Others'],
  values: [40, 25, 15, 10, 10],
};

function createLineChart() {
  const ctx = document.getElementById('storesLineChart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: storesOverview.labels,
      datasets: [{
        data: storesOverview.values,
        borderColor: '#ff944d',
        backgroundColor: 'rgba(240, 143, 79, 0.18)',
        fill: true,
        tension: 0.38,
        pointRadius: 4,
        pointBackgroundColor: '#ff944d',
      }]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#7a7f8c' } },
        y: { grid: { color: 'rgba(125, 132, 156, 0.16)' }, ticks: { color: '#7a7f8c', beginAtZero: true } }
      }
    }
  });
}

function createDonutChart() {
  const ctx = document.getElementById('categoryDonutChart').getContext('2d');
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: categoryData.labels,
      datasets: [{
        data: categoryData.values,
        backgroundColor: ['#6f80ff', '#ff9b64', '#a183ff', '#fedc62', '#8a94a6'],
        borderWidth: 0,
      }]
    },
    options: {
      cutout: '68%',
      plugins: { legend: { display: false } }
    }
  });
}

function renderOrders() {
  const container = document.getElementById('ordersTable');
  container.innerHTML = ordersData.map(order => {
    const statusClass = {
      Completed: 'badge badge-completed',
      Processing: 'badge badge-processing',
      Shipped: 'badge badge-shipped',
    }[order.status] || 'badge badge-processing';

    return `
      <tr>
        <td>${order.id}</td>
        <td>${order.customer}</td>
        <td>${order.total}</td>
        <td><span class="${statusClass}">${order.status}</span></td>
        <td>${order.date}</td>
      </tr>
    `;
  }).join('');
}

function renderLowStock() {
  const container = document.getElementById('lowStockTable');
  container.innerHTML = lowStockData.map(item => {
    const stockClass = item.stock <= 3 ? 'badge badge-lowstock' : '';
    return `
      <tr>
        <td>${item.name}</td>
        <td><span class="${stockClass}">${item.stock}</span></td>
        <td>${item.threshold}</td>
      </tr>
    `;
  }).join('');
}

function initNav() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => item.addEventListener('click', () => {
    navItems.forEach(nav => nav.classList.remove('active'));
    item.classList.add('active');
  }));
}

window.addEventListener('DOMContentLoaded', () => {
  renderOrders();
  renderLowStock();
  createLineChart();
  createDonutChart();
  initNav();
});
