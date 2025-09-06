document.addEventListener('DOMContentLoaded', function () {
  // Mobile navigation toggle
  const btn = document.getElementById('nav-toggle');
  const list = document.getElementById('main-nav-list');
  
  if (btn && list) {
    btn.addEventListener('click', function () {
      const expanded = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!expanded));
      list.classList.toggle('open');
    });
  }

  // Dropdown functionality
  const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
  
  dropdownToggles.forEach(toggle => {
    toggle.addEventListener('click', function(e) {
      e.preventDefault();
      
      const dropdownId = this.getAttribute('data-dropdown') + '-dropdown';
      const dropdown = document.getElementById(dropdownId);
      const isOpen = dropdown.classList.contains('show');
      
      // Close all other dropdowns
      document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.classList.remove('show');
      });
      document.querySelectorAll('.dropdown-toggle').forEach(t => {
        t.classList.remove('open');
      });
      
      // Toggle current dropdown
      if (!isOpen) {
        dropdown.classList.add('show');
        this.classList.add('open');
      }
    });
  });

  // Close dropdowns when clicking outside
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.nav-item.dropdown')) {
      document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.classList.remove('show');
      });
      document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
        toggle.classList.remove('open');
      });
    }
  });

  // Close mobile nav when clicking on links
  document.querySelectorAll('.nav-link, .dropdown-item').forEach(link => {
    link.addEventListener('click', function() {
      if (window.innerWidth <= 768) {
        list.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  });
});
