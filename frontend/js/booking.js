// Booking Page JavaScript

class BookingPage {
    constructor() {
        this.stylistId = this.extractStylistId();
        this.selectedTimeSlot = null;
        this.availableSlots = [];
        this.stylistData = null;
        
        this.initializePage();
    }

    extractStylistId() {
        // Extract stylist ID from URL path /book/{stylist_id}
        const pathParts = window.location.pathname.split('/');
        const stylistId = pathParts[pathParts.length - 1];
        return parseInt(stylistId);
    }

    async initializePage() {
        if (!this.stylistId || isNaN(this.stylistId)) {
            this.showError('Invalid stylist ID');
            return;
        }

        try {
            await this.loadStylistInfo();
            this.setupEventListeners();
            this.setMinDate();
            this.showBookingContent();
        } catch (error) {
            console.error('Failed to initialize booking page:', error);
            this.showError('Failed to load stylist information');
        }
    }

    async loadStylistInfo() {
        try {
            const response = await fetch(`/api/public/stylists/${this.stylistId}`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Stylist not found');
                }
                throw new Error('Failed to load stylist information');
            }

            const data = await response.json();
            this.stylistData = data.stylist;
            this.populateStylistInfo();
        } catch (error) {
            console.error('Error loading stylist info:', error);
            throw error;
        }
    }

    populateStylistInfo() {
        const stylist = this.stylistData;
        
        // Update stylist profile section
        document.getElementById('stylistBusinessName').textContent = stylist.business_name;
        document.getElementById('stylistName').textContent = stylist.name;
        document.getElementById('stylistBio').textContent = stylist.bio || 'No bio available';
        document.getElementById('stylistPhone').textContent = stylist.phone || 'Not provided';
        
        // Update profile image if provided
        if (stylist.profile_image_url) {
            document.getElementById('stylistImage').src = stylist.profile_image_url;
        }

        // Update page title
        document.title = `Book with ${stylist.business_name} - Quikka`;
    }

    setupEventListeners() {
        // Date change listener
        const dateInput = document.getElementById('appointmentDate');
        dateInput.addEventListener('change', () => this.handleDateChange());

        // Duration change listener
        const durationInput = document.getElementById('duration');
        durationInput.addEventListener('change', () => this.handleDurationChange());

        // Form submission
        const form = document.getElementById('bookingForm');
        form.addEventListener('submit', (e) => this.handleFormSubmission(e));

        // Time slot selection (delegated event listener)
        const timeSlotsContainer = document.getElementById('timeSlotsContainer');
        timeSlotsContainer.addEventListener('click', (e) => this.handleTimeSlotClick(e));
    }

    setMinDate() {
        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('appointmentDate').min = today;
    }

    async handleDateChange() {
        const dateInput = document.getElementById('appointmentDate');
        const durationInput = document.getElementById('duration');
        
        if (!dateInput.value || !durationInput.value) {
            this.showTimeSlotsPlaceholder();
            return;
        }

        await this.loadAvailableTimeSlots();
    }

    async handleDurationChange() {
        const dateInput = document.getElementById('appointmentDate');
        
        if (!dateInput.value) {
            this.showTimeSlotsPlaceholder();
            return;
        }

        await this.loadAvailableTimeSlots();
    }

    async loadAvailableTimeSlots() {
        const dateInput = document.getElementById('appointmentDate');
        const durationInput = document.getElementById('duration');
        
        const appointmentDate = dateInput.value;
        const duration = parseInt(durationInput.value);

        if (!appointmentDate || !duration) return;

        this.showTimeSlotsLoading();

        try {
            const url = `/api/public/stylists/${this.stylistId}/availability?appointment_date=${appointmentDate}&duration_minutes=${duration}`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error('Failed to load available time slots');
            }

            const data = await response.json();
            this.availableSlots = data.available_slots;
            this.displayTimeSlots();
        } catch (error) {
            console.error('Error loading time slots:', error);
            this.showTimeSlotsError();
        }
    }

    showTimeSlotsPlaceholder() {
        const container = document.getElementById('timeSlotsContainer');
        container.innerHTML = '<p class="slots-placeholder">Please select a date and duration first</p>';
        this.selectedTimeSlot = null;
    }

    showTimeSlotsLoading() {
        const container = document.getElementById('timeSlotsContainer');
        container.innerHTML = `
            <div class="slots-loading">
                <div class="loading-spinner small"></div>
                <span>Loading available slots...</span>
            </div>
        `;
    }

    showTimeSlotsError() {
        const container = document.getElementById('timeSlotsContainer');
        container.innerHTML = '<p class="slots-placeholder" style="color: #dc3545;">Failed to load time slots. Please try again.</p>';
    }

    displayTimeSlots() {
        const container = document.getElementById('timeSlotsContainer');
        
        if (this.availableSlots.length === 0) {
            container.innerHTML = '<p class="slots-placeholder">No available slots for the selected date and duration.</p>';
            return;
        }

        const slotsHTML = this.availableSlots.map(slot => `
            <button type="button" class="time-slot" data-time="${slot}">
                ${this.formatTime(slot)}
            </button>
        `).join('');

        container.innerHTML = slotsHTML;
        this.selectedTimeSlot = null;
    }

    formatTime(timeString) {
        // Convert 24-hour time to 12-hour format
        const [hours, minutes] = timeString.split(':');
        const hour = parseInt(hours);
        const period = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
        return `${displayHour}:${minutes} ${period}`;
    }

    handleTimeSlotClick(e) {
        if (!e.target.classList.contains('time-slot')) return;

        // Remove selection from all slots
        document.querySelectorAll('.time-slot').forEach(slot => {
            slot.classList.remove('selected');
        });

        // Select clicked slot
        e.target.classList.add('selected');
        this.selectedTimeSlot = e.target.dataset.time;
    }

    async handleFormSubmission(e) {
        e.preventDefault();

        if (!this.validateForm()) return;

        this.setFormLoading(true);

        try {
            const bookingData = this.collectFormData();
            const response = await fetch('/api/public/bookings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(bookingData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create booking');
            }

            const booking = await response.json();
            this.showSuccessModal(booking);
            
        } catch (error) {
            console.error('Booking submission error:', error);
            this.showErrorModal(error.message);
        } finally {
            this.setFormLoading(false);
        }
    }

    validateForm() {
        const requiredFields = [
            'serviceName', 'duration', 'appointmentDate', 
            'clientName', 'clientEmail', 'price'
        ];

        for (const fieldId of requiredFields) {
            const field = document.getElementById(fieldId);
            if (!field.value.trim()) {
                field.focus();
                this.showErrorModal(`Please fill in the ${field.labels[0].textContent.toLowerCase()}`);
                return false;
            }
        }

        if (!this.selectedTimeSlot) {
            this.showErrorModal('Please select an available time slot');
            return false;
        }

        // Validate email format
        const emailField = document.getElementById('clientEmail');
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(emailField.value)) {
            emailField.focus();
            this.showErrorModal('Please enter a valid email address');
            return false;
        }

        return true;
    }

    collectFormData() {
        return {
            stylist_id: this.stylistId,
            service_name: document.getElementById('serviceName').value.trim(),
            service_description: document.getElementById('serviceDescription').value.trim() || null,
            duration_minutes: parseInt(document.getElementById('duration').value),
            appointment_date: document.getElementById('appointmentDate').value,
            appointment_time: this.selectedTimeSlot,
            client_name: document.getElementById('clientName').value.trim(),
            client_email: document.getElementById('clientEmail').value.trim(),
            client_phone: document.getElementById('clientPhone').value.trim() || null,
            price: parseFloat(document.getElementById('price').value),
            currency: 'KES',
            notes: document.getElementById('notes').value.trim() || null
        };
    }

    setFormLoading(loading) {
        const submitBtn = document.getElementById('submitBtn');
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoading = submitBtn.querySelector('.btn-loading');

        if (loading) {
            btnText.style.display = 'none';
            btnLoading.style.display = 'flex';
            submitBtn.disabled = true;
        } else {
            btnText.style.display = 'block';
            btnLoading.style.display = 'none';
            submitBtn.disabled = false;
        }
    }

    showSuccessModal(booking) {
        const modal = document.getElementById('successModal');
        const bookingDetails = document.getElementById('bookingDetails');
        
        // Format booking details
        const appointmentDate = new Date(booking.appointment_date).toLocaleDateString();
        const appointmentTime = this.formatTime(booking.appointment_time);
        
        bookingDetails.innerHTML = `
            <div class="summary-row">
                <span class="summary-label">Service:</span>
                <span class="summary-value">${booking.service_name}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Date:</span>
                <span class="summary-value">${appointmentDate}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Time:</span>
                <span class="summary-value">${appointmentTime}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Duration:</span>
                <span class="summary-value">${booking.duration_minutes} minutes</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Price:</span>
                <span class="summary-value">KES ${booking.price}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Booking ID:</span>
                <span class="summary-value">#${booking.id}</span>
            </div>
        `;

        modal.style.display = 'flex';
    }

    showErrorModal(message) {
        const modal = document.getElementById('errorModal');
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.textContent = message;
        modal.style.display = 'flex';
    }

    showError(message) {
        const errorState = document.getElementById('errorState');
        const loadingState = document.getElementById('loadingState');
        const bookingContent = document.getElementById('bookingContent');

        loadingState.style.display = 'none';
        bookingContent.style.display = 'none';
        errorState.style.display = 'flex';
        
        // Update error message if needed
        const errorText = errorState.querySelector('p');
        if (message !== 'Stylist not found') {
            errorText.textContent = message;
        }
    }

    showBookingContent() {
        const errorState = document.getElementById('errorState');
        const loadingState = document.getElementById('loadingState');
        const bookingContent = document.getElementById('bookingContent');

        errorState.style.display = 'none';
        loadingState.style.display = 'none';
        bookingContent.style.display = 'block';
    }
}

// Modal control functions (global scope for onclick handlers)
function closeSuccessModal() {
    document.getElementById('successModal').style.display = 'none';
    // Optionally redirect to home or refresh the form
    location.reload();
}

function closeErrorModal() {
    document.getElementById('errorModal').style.display = 'none';
}

// Initialize the booking page when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new BookingPage();
});

// Close modals when clicking outside them
window.addEventListener('click', (e) => {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});