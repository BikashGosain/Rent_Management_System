// ===================== SIDEBAR DROPDOWN =====================
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
    const isOpen = dropdown.classList.contains("open");
    closeAllDropdowns();
    toggleDropdown(dropdown, menu, !isOpen);
  });
});

// ===================== SIDEBAR TOGGLE =====================
const sidebar = document.querySelector(".sidebar");
const overlay = document.querySelector(".sidebar-overlay");
const isMobile = () => window.innerWidth <= 768;

document.querySelectorAll(".sidebar-toggler").forEach((button) => {
  button.addEventListener("click", () => {
    closeAllDropdowns();
    if (isMobile()) {
      sidebar.classList.remove("mobile-open");
      overlay.classList.remove("active");
    } else {
      sidebar.classList.toggle("collapsed");
    }
  });
});

document.querySelector(".sidebar-menu-button").addEventListener("click", () => {
  closeAllDropdowns();
  sidebar.classList.toggle("mobile-open");
  overlay.classList.toggle("active");
});

// Close sidebar when overlay is clicked (mobile)
overlay.addEventListener("click", () => {
  sidebar.classList.remove("mobile-open");
  overlay.classList.remove("active");
});

// Collapse on medium screens by default
if (window.innerWidth <= 1024 && window.innerWidth > 768) {
  sidebar.classList.add("collapsed");
}

// Handle resize
let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    if (!isMobile()) {
      sidebar.classList.remove("mobile-open");
      overlay.classList.remove("active");
    }
  }, 150);
});

// ===================== PROFILE DROPDOWN =====================
const profileToggle = document.getElementById("profileToggle");
const profileDropdown = document.getElementById("profileDropdown");
const profileWrapper = profileToggle.closest(".user-profile-wrapper");

profileToggle.addEventListener("click", (e) => {
  e.stopPropagation();
  profileWrapper.classList.toggle("open");
});

// Close profile dropdown when clicking outside
document.addEventListener("click", (e) => {
  if (!profileWrapper.contains(e.target)) {
    profileWrapper.classList.remove("open");
  }
});

// Close profile dropdown on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    profileWrapper.classList.remove("open");
  }
});