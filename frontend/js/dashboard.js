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
      
      // Load time slots for selected date - create date string directly to avoid timezone issues
      const dateString = `${year}-${(month + 1).toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
      const selectedDate = new Date(dateString + 'T12:00:00'); // Use noon to avoid timezone shifts
      loadTimeSlotsForDate(selectedDate);
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
    
    // Load time slots for today by default
    loadTimeSlotsForDate(new Date());
    
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

// Load time slots for a specific date
async function loadTimeSlotsForDate(selectedDate) {
  // Create date string directly to avoid timezone conversion issues
  const year = selectedDate.getFullYear();
  const month = (selectedDate.getMonth() + 1).toString().padStart(2, '0');
  const day = selectedDate.getDate().toString().padStart(2, '0');
  const dateString = `${year}-${month}-${day}`;
  
  const displayDate = selectedDate.toLocaleDateString('en-US', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  });
  
  // Update the date display
  document.getElementById('selectedDateDisplay').textContent = displayDate;
  
  // Show loading state
  const container = document.getElementById('timeSlotsContainer');
  container.innerHTML = '<p class="loading-slots">Loading time slots...</p>';
  
  try {
    // Get current user to extract stylist ID
    const userResponse = await authenticatedRequest('http://localhost:8000/api/profile');
    const stylistId = userResponse.user.stylist_profile?.id;
    
    if (!stylistId) {
      container.innerHTML = '<p class="loading-slots">Only stylists can view time slots</p>';
      return;
    }
    
    // Load available time slots
    const availabilityResponse = await authenticatedRequest(
      `http://localhost:8000/api/stylists/${stylistId}/available-times?appointment_date=${dateString}`
    );
    
    // Load bookings for this date
    const bookingsResponse = await authenticatedRequest('http://localhost:8000/api/bookings');
    
    // Debug: Log all bookings to see their format
    console.log('All bookings:', bookingsResponse.bookings);
    console.log('Looking for date:', dateString);
    
    const dayBookings = bookingsResponse.bookings.filter(booking => {
      // Log each booking date for comparison
      console.log(`Booking date: "${booking.appointment_date}" vs Target: "${dateString}"`);
      
      // Try multiple date format comparisons
      const bookingDate = booking.appointment_date;
      
      // Handle different date formats
      let matches = false;
      
      // Direct string match
      if (bookingDate === dateString) {
        matches = true;
      }
      
      // Try parsing both dates and comparing
      const bookingDateObj = new Date(bookingDate);
      const targetDateObj = new Date(dateString);
      
      if (bookingDateObj.toISOString().split('T')[0] === targetDateObj.toISOString().split('T')[0]) {
        matches = true;
      }
      
      if (matches) {
        console.log(`✓ MATCH FOUND: ${booking.client_name} at ${booking.appointment_time}`);
      }
      
      return matches;
    });
    
    console.log(`Found ${dayBookings.length} bookings for ${dateString}:`, dayBookings);
    
    displayTimeSlots(availabilityResponse.available_slots, dayBookings);
    
  } catch (error) {
    console.error('Failed to load time slots:', error);
    container.innerHTML = `<p class="loading-slots">Failed to load time slots: ${error.message}</p>`;
  }
}

// Display time slots with booking status
function displayTimeSlots(availableSlots, bookings) {
  const container = document.getElementById('timeSlotsContainer');
  
  if (!availableSlots || availableSlots.length === 0) {
    container.innerHTML = '<p class="loading-slots">No available time slots for this date</p>';
    return;
  }
  
  // Debug: Log the data formats
  console.log('Available slots format:', availableSlots[0]);
  console.log('Bookings passed to displayTimeSlots:', bookings);
  console.log('Number of bookings for this date:', bookings.length);
  
  if (bookings.length > 0) {
    console.log('First booking format:', bookings[0]);
  }
  
  // Create a map of booked times for quick lookup
  const bookedTimes = new Map();
  bookings.forEach(booking => {
    // Normalize booking time to HH:MM format
    let timeKey;
    
    // Handle different time formats
    if (booking.appointment_time.includes('AM') || booking.appointment_time.includes('PM')) {
      // Convert "10:00 AM" to "10:00"
      const time12 = booking.appointment_time;
      const [time, period] = time12.split(' ');
      const [hours, minutes] = time.split(':');
      let hour24 = parseInt(hours);
      
      if (period === 'PM' && hour24 !== 12) {
        hour24 += 12;
      } else if (period === 'AM' && hour24 === 12) {
        hour24 = 0;
      }
      
      timeKey = `${hour24.toString().padStart(2, '0')}:${minutes}`;
    } else if (booking.appointment_time.includes(':')) {
      // Handle "HH:MM:SS" or "HH:MM" format
      timeKey = booking.appointment_time.substring(0, 5); // Get HH:MM
    } else {
      timeKey = booking.appointment_time;
    }
    
    console.log(`Booking time: ${booking.appointment_time} -> ${timeKey}`);
    bookedTimes.set(timeKey, booking);
  });
  
  container.innerHTML = '';
  
  availableSlots.forEach(slot => {
    const slotElement = document.createElement('div');
    const booking = bookedTimes.get(slot.start_time);
    const isBooked = !!booking;
    
    console.log(`Slot ${slot.start_time}: ${isBooked ? 'BOOKED' : 'available'}`);
    
    slotElement.className = `time-slot ${isBooked ? 'booked' : 'available'}`;
    
    slotElement.innerHTML = `
      <div class="slot-info">
        <div class="slot-time">${slot.start_time} - ${slot.end_time}</div>
        ${isBooked ? `<div class="slot-client">${booking.client_name}</div>` : ''}
      </div>
      <div class="slot-status ${isBooked ? 'booked' : 'available'}">
        ${isBooked ? 'Booked' : 'Available'}
      </div>
    `;
    
    container.appendChild(slotElement);
  });
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