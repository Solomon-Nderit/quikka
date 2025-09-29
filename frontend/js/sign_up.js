(function(){
  const signupForm = document.getElementById('signupForm');
  const loginForm = document.getElementById('loginForm');
  const toLogin = document.getElementById('toLogin');
  const toSignup = document.getElementById('toSignup');
  const title = document.getElementById('formTitle');
  const caption = document.getElementById('formCaption');
  const navLoginBtn = document.getElementById('navLoginBtn');
  const roleSelect = document.getElementById('su-role');
  const stylistFields = document.getElementById('stylistFields');

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
        // Basic JWT structure check
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

  // Show/hide stylist fields based on role selection
  roleSelect.addEventListener('change', function() {
    const businessField = document.getElementById('su-business');
    const bioField = document.getElementById('su-bio');
    
    if (this.value === 'stylist') {
      stylistFields.style.display = 'block';
      businessField.required = true;
      bioField.required = true;
    } else {
      stylistFields.style.display = 'none';
      businessField.required = false;
      bioField.required = false;
    }
  });

  function show(mode){
    const isSignup = mode === 'signup';
    signupForm.style.display = isSignup ? 'flex' : 'none';
    loginForm.style.display = isSignup ? 'none' : 'flex';
    title.textContent = isSignup ? 'Sign up for free' : 'Welcome back';
    caption.textContent = isSignup ? 'Use 6+ characters with a mix of letters and numbers.' : 'Enter your credentials to continue.';
    // Reflect state in URL hash without reloading
    history.replaceState(null, '', isSignup ? '#signup' : '#login');
  }

  // Check if user is already authenticated
  if (TokenManager.isAuthenticated()) {
    // Redirect to dashboard if already logged in
    window.location.href = '/dashboard';
    return;
  }

  // Initial state based on hash
  if (location.hash === '#login') show('login'); else show('signup');

  toLogin.addEventListener('click', e => { e.preventDefault(); show('login'); });
  toSignup.addEventListener('click', e => { e.preventDefault(); show('signup'); });
  navLoginBtn.addEventListener('click', e => { e.preventDefault(); show('login'); });

  // API request helper
  async function apiRequest(url, data) {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    const responseData = await response.json().catch(() => ({}));
    
    if (!response.ok) {
      const errorMessage = responseData.detail || responseData.message || `Request failed (${response.status})`;
      throw new Error(errorMessage);
    }
    
    return responseData;
  }

  // Signup form handler
  signupForm.addEventListener('submit', async e => {
    e.preventDefault();
    
    const formData = new FormData(signupForm);
    const data = Object.fromEntries(formData.entries());
    
    // Remove empty fields
    Object.keys(data).forEach(key => {
      if (!data[key]) delete data[key];
    });
    
    const submitBtn = signupForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Signing up...';
    
    try {
      const response = await apiRequest('http://localhost:8000/api/signup', data);
      alert('Sign up successful! Please log in with your credentials.');
      show('login');
      signupForm.reset();
    } catch (err) {
      alert('Sign up failed: ' + err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  });

  // Login form handler
  loginForm.addEventListener('submit', async e => {
    e.preventDefault();
    
    const email = document.getElementById('li-email').value.trim();
    const password = document.getElementById('li-password').value;
    
    const submitBtn = loginForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Logging in...';
    
    try {
      const response = await apiRequest('http://localhost:8000/api/login', { email, password });
      
      // Store JWT token
      if (response.access_token) {
        TokenManager.setToken(response.access_token);
        alert(`Welcome back, ${response.user.name}!`);
        
        // Redirect to dashboard
        window.location.href = 'http://localhost:8000/dashboard';
      } else {
        throw new Error('No access token received');
      }
    } catch (err) {
      alert('Login failed: ' + err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  });
})();