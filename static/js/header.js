document.addEventListener('DOMContentLoaded', () => {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    // Initially hide the mobile menu
    mobileMenu.classList.add('hidden');

    // Toggle mobile menu visibility
    mobileMenuButton.addEventListener('click', () => {
        mobileMenu.classList.toggle('hidden'); // Toggle 'hidden' class
        mobileMenu.classList.toggle('show');   // Toggle 'show' class for any additional styles
        // Update aria-expanded attribute
        const isExpanded = mobileMenu.classList.contains('hidden');
        mobileMenuButton.setAttribute('aria-expanded', !isExpanded);
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', (event) => {
        if (!mobileMenu.contains(event.target) && !mobileMenuButton.contains(event.target)) {
            mobileMenu.classList.add('hidden'); // Hide the menu
            mobileMenuButton.setAttribute('aria-expanded', 'false'); // Update aria attribute
        }
    });
});
