document.addEventListener('DOMContentLoaded', function() {
    const currentPage = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPage || (linkPath !== "/" && currentPage.startsWith(linkPath))) {
            link.classList.add('me');
        }
    });
});
