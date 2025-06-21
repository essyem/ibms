document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-picker').forEach(button => {
        button.addEventListener('click', function() {
            const grid = this.nextElementSibling;
            grid.style.display = grid.style.display === 'none' ? 'grid' : 'none';
        });
    });

    document.querySelectorAll('.icon-grid i').forEach(icon => {
        icon.addEventListener('click', function() {
            const input = this.closest('.icon-picker-container').querySelector('input');
            input.value = this.dataset.value;
            this.closest('.icon-picker-container').querySelector('.icon-preview i').className = `fas ${this.dataset.value}`;
        });
    });
});