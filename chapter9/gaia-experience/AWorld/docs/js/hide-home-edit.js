// Check if the current page is the home page, if so hide the edit link
if (window.location.pathname === '/' ||
    window.location.pathname.endsWith('/index.html') ||
    window.location.pathname.endsWith('/AWorld/')) {
  const editLink = document.querySelector('.wy-breadcrumbs-aside a[href*="index.md"]');
  if (editLink) {
    editLink.style.display = 'none';
  }
}