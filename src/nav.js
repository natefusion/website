/* gipity */
document.addEventListener('DOMContentLoaded', function() {
    const currentPage = window.location.pathname; // Get the current path

    const navLinks = document.querySelectorAll('nav a'); // Select all links in your navbar

    navLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname; // Extract the path from the link's href

        const home_page = linkPath == "/index.html" && currentPage == "/";
        if (home_page || linkPath === currentPage || (linkPath !== "/" && currentPage.startsWith(linkPath + "/"))) {
            link.classList.add('me'); // Add the 'active' class to the matching link
        }
    });
});
