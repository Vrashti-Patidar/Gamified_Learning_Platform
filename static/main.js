// Toggle between login and signup forms within the auth modal
function showLogin() {
    const container = document.getElementById('authFormContainer');
    const template = document.getElementById('loginTemplate');
    if (container && template) {
        container.innerHTML = template.innerHTML;
        document.getElementById('authToggleText').innerHTML = 'Don\'t have an account? <a href="#" class="text-primary text-decoration-none fw-bold" onclick="showSignup(event)">Sign up here</a>';
    }
}

function showSignup(event) {
    if (event) event.preventDefault();
    const container = document.getElementById('authFormContainer');
    const template = document.getElementById('signupTemplate');
    if (container && template) {
        container.innerHTML = template.innerHTML;
        document.getElementById('authToggleText').innerHTML = 'Already have an account? <a href="#" class="text-primary text-decoration-none fw-bold" onclick="showLogin(event)">Login here</a>';
        
        // Attach form validation logic
        const form = document.getElementById('signupForm');
        form.addEventListener('submit', validateSignup);
    }
}

// Ensure login is shown by default if just toggled without event
function toggleAuthMode(event) {
    event.preventDefault();
    showSignup(event); // the default mode is login, so toggling goes to signup
}

function validateSignup(event) {
    const password = document.getElementById('signupPassword').value;
    const confirmPassword = document.getElementById('signupConfirmPassword').value;
    
    if (password !== confirmPassword) {
        event.preventDefault();
        document.getElementById('signupConfirmPassword').classList.add('is-invalid');
        return false;
    } else {
        document.getElementById('signupConfirmPassword').classList.remove('is-invalid');
    }
    
    const captchaCheck = document.getElementById('captchaCheck');
    if (!captchaCheck.checked) {
        event.preventDefault();
        alert('Please verify you are a human.');
        return false;
    }
    
    return true;
}

// Auto-hide alerts/toasts after 5 seconds
document.addEventListener("DOMContentLoaded", function(){
    let toasts = document.querySelectorAll('.toast');
    toasts.forEach(function(toast) {
        setTimeout(function(){
            toast.classList.remove('show');
        }, 5000);
    });
});
