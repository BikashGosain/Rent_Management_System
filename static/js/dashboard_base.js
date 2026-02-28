// ===================== SIDEBAR NAV DROPDOWNS =====================
const toggleDropdown = (dropdown, menu, isOpen) => {
  dropdown.classList.toggle("open", isOpen);
  menu.style.height = isOpen ? `${menu.scrollHeight}px` : 0;
};

const closeAllDropdowns = () => {
  document.querySelectorAll(".dropdown-container.open").forEach((openDropdown) => {
    toggleDropdown(openDropdown, openDropdown.querySelector(".dropdown-menu"), false);
  });
};

document.querySelectorAll(".dropdown-toggle").forEach((dropdownToggle) => {
  dropdownToggle.addEventListener("click", (e) => {
    e.preventDefault();
    const dropdown = dropdownToggle.closest(".dropdown-container");
    const menu = dropdown.querySelector(".dropdown-menu");
    const wasOpen = dropdown.classList.contains("open");
    closeAllDropdowns();
    if (!wasOpen) {
      toggleDropdown(dropdown, menu, true);
    }
  });
});

// ===================== SIDEBAR TOGGLE =====================
// The sidebar is ALWAYS visible on screen at every screen size.
// On desktop (>768px): toggle between full (270px) and icon-only (85px) using "collapsed" class.
// On mobile (≤768px): starts icon-only, toggle between icon-only (85px) and full (270px) using "expanded" class.

const sidebar = document.querySelector(".sidebar");
const isMobile = () => window.innerWidth <= 768;

// The chevron button inside the sidebar is the ONLY toggle
document.querySelectorAll(".sidebar-toggler").forEach((btn) => {
  btn.addEventListener("click", () => {
    closeAllDropdowns();
    if (isMobile()) {
      // On mobile: toggle expanded (full width) vs default (icon-only)
      sidebar.classList.toggle("expanded");
    } else {
      // On desktop: toggle collapsed (icon-only) vs default (full width)
      sidebar.classList.toggle("collapsed");
    }
  });
});

// On page load: collapse on tablet, icon-only on mobile
function initSidebar() {
  if (window.innerWidth <= 768) {
    sidebar.classList.remove("collapsed");
    sidebar.classList.remove("expanded");
    // Mobile starts as icon-only — CSS handles this via media query default
  } else if (window.innerWidth <= 1024) {
    sidebar.classList.add("collapsed");
    sidebar.classList.remove("expanded");
  } else {
    sidebar.classList.remove("collapsed");
    sidebar.classList.remove("expanded");
  }
}

initSidebar();

// Re-init on resize
let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(initSidebar, 150);
});

// ===================== PROFILE DROPDOWN =====================
const profileToggle = document.getElementById("profileToggle");
const profileWrapper = document.getElementById("profileWrapper");

if (profileToggle && profileWrapper) {
  const profileDropdown = document.getElementById("profileDropdown");

  profileToggle.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = profileWrapper.classList.contains("open");
    if (!isOpen) {
      // Position dropdown just below the button using fixed coords
      const rect = profileToggle.getBoundingClientRect();
      profileDropdown.style.top = (rect.bottom + 8) + "px";
      profileDropdown.style.right = (window.innerWidth - rect.right) + "px";
    }
    profileWrapper.classList.toggle("open");
  });

  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (!profileWrapper.contains(e.target)) {
      profileWrapper.classList.remove("open");
    }
  });

  // Close on Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      profileWrapper.classList.remove("open");
    }
  });
}

// ── Highlight active nav link ──
const currentPath = window.location.pathname;
document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
    if (link.href && link.getAttribute('href') !== '#') {
        const linkPath = new URL(link.href).pathname;
        if (currentPath.startsWith(linkPath) && linkPath !== '/') {
            link.classList.add('active');
            // Open parent dropdown if child is active
            const parentDropdown = link.closest('.dropdown-container');
            if (parentDropdown) {
                const menu = parentDropdown.querySelector('.dropdown-menu');
                toggleDropdown(parentDropdown, menu, true);
            }
        }
    }
});