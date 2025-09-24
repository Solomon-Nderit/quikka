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
  
  // Get today's date components to avoid timezone issues
  const now = new Date();
  const todayYear = now.getFullYear();
  const todayMonth = now.getMonth();
  const todayDate = now.getDate();
  
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
    
    // Check if this is today by comparing year, month, and date directly
    if (year === todayYear && month === todayMonth && day === todayDate) {
      dayElement.classList.add('today');
    }
    
    // Add click handler for date selection
    dayElement.addEventListener('click', function() {
      // Remove previous selection
      document.querySelectorAll('.calendar-day.selected').forEach(el => 
        el.classList.remove('selected'));
      // Add selection to clicked day
      this.classList.add('selected');
      
      // Future: Could filter bookings by selected date
      console.log(`Selected date: ${year}-${(month + 1).toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`);
    });
    
    grid.appendChild(dayElement);
  }
}

// API request helper with authentication
async function authenticatedRequest(url, method = 'GET', data = null) {
  const token = TokenManager.getToken();
  
  const requestOptions = {
    method: method,
    headers: { 
      'Authorization': `Bearer ${token}`,
      'Accept': 'application/json'
    }
  };
  
  // Add Content-Type and body for non-GET requests
  if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
    requestOptions.headers['Content-Type'] = 'application/json';
    requestOptions.body = JSON.stringify(data);
  }
  
  const response = await fetch(url, requestOptions);
  
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
    
    // Calendar initialized for booking selection
    
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

// Time slots functionality removed - using appointments table only

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
    
    // Generate action buttons based on booking status
    const actionButtons = generateActionButtons(booking);
    
    row.innerHTML = `
      <td>${booking.client_name}</td>
      <td>${booking.service_name}</td>
      <td>${new Date(booking.appointment_date).toLocaleDateString()}</td>
      <td>${booking.appointment_time}</td>
      <td>
        <div class="status-actions-cell">
          <span class="status-badge status-${booking.status.toLowerCase()}">${booking.status}</span>
          <div class="booking-actions">
            ${actionButtons}
          </div>
        </div>
      </td>
    `;
    tableBody.appendChild(row);
  });
}

function generateActionButtons(booking) {
  const status = booking.status.toLowerCase();
  let buttons = '';
  
  switch (status) {
    case 'pending':
      buttons = `
        <button class="btn-action btn-confirm" onclick="updateBookingStatus(${booking.id}, 'confirmed')">Confirm</button>
        <button class="btn-action btn-cancel" onclick="updateBookingStatus(${booking.id}, 'cancelled')">Cancel</button>
        <button class="btn-action btn-reschedule" onclick="openRescheduleModal(${booking.id})">Reschedule</button>
      `;
      break;
      
    case 'confirmed':
      buttons = `
        <button class="btn-action btn-complete" onclick="updateBookingStatus(${booking.id}, 'completed')">Complete</button>
        <button class="btn-action btn-cancel" onclick="updateBookingStatus(${booking.id}, 'cancelled')">Cancel</button>
        <button class="btn-action btn-reschedule" onclick="openRescheduleModal(${booking.id})">Reschedule</button>
      `;
      break;
      
    case 'reschedule_requested':
      buttons = `
        <button class="btn-action btn-confirm" onclick="updateBookingStatus(${booking.id}, 'confirmed')">Approve</button>
        <button class="btn-action btn-cancel" onclick="updateBookingStatus(${booking.id}, 'cancelled')">Decline</button>
      `;
      break;
      
    case 'completed':
      buttons = `<span style="color: #666; font-size: 0.75rem;">Completed</span>`;
      break;
      
    case 'cancelled':
      buttons = `<span style="color: #666; font-size: 0.75rem;">Cancelled</span>`;
      break;
      
    case 'no_show':
      buttons = `<span style="color: #666; font-size: 0.75rem;">No Show</span>`;
      break;
      
    default:
      buttons = `<span style="color: #666; font-size: 0.75rem;">-</span>`;
  }
  
  return buttons;
}

// Booking status management functions
async function updateBookingStatus(bookingId, newStatus) {
  const confirmMessage = `Are you sure you want to mark this booking as ${newStatus}?`;
  
  if (!confirm(confirmMessage)) {
    return;
  }
  
  try {
    const response = await authenticatedRequest(`http://localhost:8000/api/bookings/${bookingId}/status`, 'PUT', {
      status: newStatus,
      reason: `Status updated by stylist to ${newStatus}`
    });
    
    alert(`Booking status updated to ${newStatus} successfully!`);
    
    // Reload the bookings table
    loadDashboard();
    
  } catch (error) {
    console.error('Failed to update booking status:', error);
    alert('Failed to update booking status: ' + error.message);
  }
}

// Reschedule modal functionality
let currentRescheduleBookingId = null;

function openRescheduleModal(bookingId) {
  currentRescheduleBookingId = bookingId;
  const modal = document.getElementById('rescheduleModal');
  modal.classList.add('active');
  
  // Set minimum date to tomorrow without timezone issues
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  
  // Format date as YYYY-MM-DD without timezone conversion
  const year = tomorrow.getFullYear();
  const month = (tomorrow.getMonth() + 1).toString().padStart(2, '0');
  const day = tomorrow.getDate().toString().padStart(2, '0');
  const tomorrowString = `${year}-${month}-${day}`;
  
  document.getElementById('newDate').min = tomorrowString;
  
  // Reset the time slot dropdown
  const timeSlotSelect = document.getElementById('newTimeSlot');
  timeSlotSelect.innerHTML = '<option value="">Select a date first...</option>';
}

function closeRescheduleModal() {
  const modal = document.getElementById('rescheduleModal');
  modal.classList.remove('active');
  currentRescheduleBookingId = null;
  
  // Reset form
  document.getElementById('rescheduleForm').reset();
  const timeSlotSelect = document.getElementById('newTimeSlot');
  timeSlotSelect.innerHTML = '<option value="">Select a date first...</option>';
}

// Load available slots for reschedule modal when date is selected
async function loadAvailableSlots() {
  const dateInput = document.getElementById('newDate');
  const timeSlotSelect = document.getElementById('newTimeSlot');
  const slotsLoading = document.getElementById('slotsLoading');
  
  if (!dateInput.value) {
    timeSlotSelect.innerHTML = '<option value="">Select a date first...</option>';
    return;
  }
  
  // Show loading state
  timeSlotSelect.innerHTML = '<option value="">Loading...</option>';
  timeSlotSelect.disabled = true;
  slotsLoading.style.display = 'block';
  
  try {
    // Get current user to extract stylist ID
    const userResponse = await authenticatedRequest('http://localhost:8000/api/profile');
    const stylistId = userResponse.user.stylist_profile?.id;
    
    if (!stylistId) {
      timeSlotSelect.innerHTML = '<option value="">Only stylists can reschedule</option>';
      slotsLoading.style.display = 'none';
      return;
    }
    
    // Load available time slots for the selected date
    const availabilityResponse = await authenticatedRequest(
      `http://localhost:8000/api/stylists/${stylistId}/available-times?appointment_date=${dateInput.value}`
    );
    
    // Populate the dropdown with available slots
    timeSlotSelect.innerHTML = '';
    
    if (availabilityResponse.available_slots && availabilityResponse.available_slots.length > 0) {
      // Add default option
      const defaultOption = document.createElement('option');
      defaultOption.value = '';
      defaultOption.textContent = 'Select a time slot...';
      timeSlotSelect.appendChild(defaultOption);
      
      // Add available slots
      availabilityResponse.available_slots.forEach(slot => {
        const option = document.createElement('option');
        option.value = slot.start_time;
        option.textContent = `${slot.start_time} - ${slot.end_time}`;
        timeSlotSelect.appendChild(option);
      });
    } else {
      timeSlotSelect.innerHTML = '<option value="">No available slots for this date</option>';
    }
    
  } catch (error) {
    console.error('Failed to load available slots:', error);
    timeSlotSelect.innerHTML = '<option value="">Failed to load slots</option>';
  } finally {
    timeSlotSelect.disabled = false;
    slotsLoading.style.display = 'none';
  }
}

// Handle reschedule form submission
document.addEventListener('DOMContentLoaded', function() {
  const rescheduleForm = document.getElementById('rescheduleForm');
  if (rescheduleForm) {
    rescheduleForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      if (!currentRescheduleBookingId) {
        alert('No booking selected for rescheduling');
        return;
      }
      
      const formData = new FormData(rescheduleForm);
      const rescheduleData = {
        new_appointment_date: formData.get('new_appointment_date'),
        new_appointment_time: formData.get('new_appointment_time'),
        reschedule_reason: formData.get('reschedule_reason')
      };
      
      try {
        const response = await authenticatedRequest(
          `http://localhost:8000/api/bookings/${currentRescheduleBookingId}/reschedule`, 
          'POST', 
          rescheduleData
        );
        
        alert('Booking rescheduled successfully!');
        closeRescheduleModal();
        loadDashboard(); // Reload the bookings
        
      } catch (error) {
        console.error('Failed to reschedule booking:', error);
        alert('Failed to reschedule booking: ' + error.message);
      }
    });
  }
  
  // Initialize dashboard
  updateCalendarDisplay();
  loadDashboard();
});

// Sidebar toggle functionality
function toggleSidebar() {
  const sidebar = document.querySelector('.sidebar');
  const toggle = document.querySelector('.sidebar-toggle');
  
  sidebar.classList.toggle('expanded');
  
  // Update toggle icon
  if (sidebar.classList.contains('expanded')) {
    toggle.textContent = '✕'; // Close icon
  } else {
    toggle.textContent = '☰'; // Menu icon
  }
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