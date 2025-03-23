document.addEventListener('DOMContentLoaded', function() {
  const sidebarToggle = document.querySelector('.sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  let isMobile = window.innerWidth < 1024;

  // Handle toggle
  sidebarToggle.addEventListener('click', function(e) {
    e.stopPropagation();
    sidebar.classList.toggle('sidebar-hidden');
  });

  // Handle auto-close hanya di mobile
  document.addEventListener('click', function(e) {
    if (!isMobile) return;

    if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
      sidebar.classList.add('sidebar-hidden');
    }
  });

  // Update status mobile saat resize
  window.addEventListener('resize', () => {
    isMobile = window.innerWidth < 1024;
  });
});