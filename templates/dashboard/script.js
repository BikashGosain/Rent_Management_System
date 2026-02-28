// ===================== SIDEBAR DROPDOWN (nav items) =====================
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
const sidebar = document.querySelector(".sidebar");
const overlay = document.querySelector(".sidebar-overlay");

const isMobile = () => window.innerWidth <= 768;

// The button inside the header (always visible)
document.getElementById("sidebarToggleBtn").addEventListener("click", () => {
  closeAllDropdowns();
  if (isMobile()) {
    // Mobile: slide in/out
    const isOpen = sidebar.classList.contains("mobile-open");
    sidebar.classList.toggle("mobile-open", !isOpen);
    overlay.classList.toggle("active", !isOpen);
  } else {
    // Desktop/tablet: collapse to icon-only
    sidebar.classList.toggle("collapsed");
  }
});

// The chevron button inside the sidebar itself
document.querySelectorAll(".sidebar-toggler").forEach((btn) => {
  btn.addEventListener("click", () => {
    closeAllDropdowns();
    if (isMobile()) {
      // Close the sidebar on mobile
      sidebar.classList.remove("mobile-open");
      overlay.classList.remove("active");
    } else {
      sidebar.classList.toggle("collapsed");
    }
  });
});

// Close sidebar when clicking overlay (mobile)
overlay.addEventListener("click", () => {
  sidebar.classList.remove("mobile-open");
  overlay.classList.remove("active");
});

// Auto-collapse on tablet (769–1024px), leave mobile alone
if (window.innerWidth > 768 && window.innerWidth <= 1024) {
  sidebar.classList.add("collapsed");
}

// Handle window resize
let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    if (!isMobile()) {
      // Clean up mobile state when resizing to desktop
      sidebar.classList.remove("mobile-open");
      overlay.classList.remove("active");
    } else {
      // Clean up desktop collapsed state when resizing to mobile
      sidebar.classList.remove("collapsed");
    }
  }, 150);
});

// ===================== PROFILE DROPDOWN =====================
const profileToggle = document.getElementById("profileToggle");
const profileWrapper = document.getElementById("profileWrapper");

profileToggle.addEventListener("click", (e) => {
  e.stopPropagation();
  profileWrapper.classList.toggle("open");
});

// Close when clicking anywhere outside
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