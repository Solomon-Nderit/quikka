// JWT Token Management
const TokenManager = {
  setToken: function(token) {
    localStorage.setItem('quikka_token', token);
  },
  getToken: function() {
    return localStorage.getItem('quikka_token');
  },
  removeToken: function() {
    localStorage.removeItem('quikka_token');
  },
  isAuthenticated: function() {
    const token = this.getToken();
    if (!token) return false;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp > currentTime;
    } catch (error) {
      console.error('Invalid token:', error);
      this.removeToken();
      return false;
    }
  }
};

// Check authentication on page load
if (!TokenManager.isAuthenticated()) {
  alert('Please log in to access the dashboard');
  window.location.href = '/auth';
}

// Calendar functionality
let currentDate = new Date(); // Start with current month

function updateCalendarDisplay() {
  document.getElementById('currentMonth').textContent = 
    currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  generateCalendar();
}

function previousMonth() {
  currentDate.setMonth(currentDate.getMonth() - 1);
  updateCalendarDisplay();
}

function nextMonth() {
  currentDate.setMonth(currentDate.getMonth() + 1);
  updateCalendarDisplay();
}

function generateCalendar() {
  const grid = document.getElementById('calendarGrid');
  
  // Remove all existing calendar days (keep the headers)
  const existingDays = grid.querySelectorAll('.calendar-day, .calendar-day.other-month');
  existingDays.forEach(day => day.remove());
  
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const today = new Date();
  
  // Add empty cells for days before the first day of the month
  for (let i = 0; i < firstDay; i++) {
    const emptyDay = document.createElement('div');
    emptyDay.className = 'calendar-day other-month';
    grid.appendChild(emptyDay);
  }
  
  // Add days of the month
  for (let day = 1; day <= daysInMonth; day++) {
    const dayElement = document.createElement('div');
    dayElement.className = 'calendar-day';
    dayElement.textContent = day;
    
    const currentDateCheck = new Date(year, month, day);
    if (currentDateCheck.toDateString() === today.toDateString()) {
      dayElement.classList.add('today');
    }
    
    // Add click handler for future booking integration
    dayElement.addEventListener('click', function() {
      // Remove previous selection
      document.querySelectorAll('.calendar-day.selected').forEach(el => 
        el.classList.remove('selected'));
      // Add selection to clicked day
      this.classList.add('selected');
    });
    
    grid.appendChild(dayElement);
  }
}

// API request helper with authentication
async function authenticatedRequest(url) {
  const token = TokenManager.getToken();
  
  const response = await fetch(url, {
    method: 'GET',
    headers: { 
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json'
    }
  });
  
  if (response.status === 401) {
    TokenManager.removeToken();
    alert('Your session has expired. Please log in again.');
    window.location.href = '/auth';
    return;
  }
  
  const responseData = await response.json().catch(() => ({}));
  
  if (!response.ok) {
    const errorMessage = responseData.detail || responseData.message || `Request failed (${response.status})`;
    throw new Error(errorMessage);
  }
  
  return responseData;
}

// Load dashboard data
async function loadDashboard() {
  try {
    // Load user profile
    const userResponse = await authenticatedRequest('http://localhost:8000/api/profile');
    updateUserProfile(userResponse.user);
    
    // Load bookings
    const bookingsResponse = await authenticatedRequest('http://localhost:8000/api/bookings');
    updateBookingsTable(bookingsResponse.bookings);
    
    // Hide loading, show content
    document.getElementById('loading').style.display = 'none';
    document.getElementById('dashboardContent').style.display = 'block';
    
  } catch (error) {
    console.error('Dashboard load error:', error);
    document.getElementById('loading').style.display = 'none';
    document.getElementById('error').style.display = 'block';
    document.querySelector('#error p').textContent = 'Failed to load dashboard: ' + error.message;
  }
}

function updateUserProfile(user) {
  document.getElementById('userAvatar').textContent = user.name.charAt(0).toUpperCase();
  document.getElementById('userName').textContent = user.name;
  document.getElementById('userRole').textContent = user.role.charAt(0).toUpperCase() + user.role.slice(1);
}

function updateBookingsTable(bookings) {
  const tableBody = document.getElementById('bookingsTableBody');
  tableBody.innerHTML = '';
  
  if (!bookings || bookings.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="5" style="text-align: center; padding: 2rem; color: #666;">
          No upcoming bookings found
        </td>
      </tr>
    `;
    return;
  }
  
  bookings.forEach(booking => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${booking.client_name}</td>
      <td>${booking.service_name}</td>
      <td>${new Date(booking.appointment_date).toLocaleDateString()}</td>
      <td>${booking.appointment_time}</td>
      <td><span class="status-badge status-${booking.status.toLowerCase()}">${booking.status}</span></td>
    `;
    tableBody.appendChild(row);
  });
}

// Navigation functions
function navigateTo(section) {
  // Update active nav item
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
  });
  event.target.closest('.nav-item').classList.add('active');
  
  // For now, just update the title
  document.querySelector('.content-title').textContent = 
    section.charAt(0).toUpperCase() + section.slice(1);
}

// Logout functionality
async function logout() {
  try {
    await authenticatedRequest('http://localhost:8000/api/logout');
  } catch (error) {
    console.error('Logout request failed:', error);
  } finally {
    TokenManager.removeToken();
    alert('You have been logged out successfully');
    window.location.href = '/auth';
  }
}

// Initialize the page when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  updateCalendarDisplay();
  loadDashboard();
});