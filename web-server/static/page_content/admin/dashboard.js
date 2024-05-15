document.addEventListener('DOMContentLoaded', (event) => {
    let currentPage = 1;
    const perPage = 10;

    function fetchUsers(page) {
        fetch(`/admin/users?page=${page}&per_page=${perPage}`)
            .then(response => response.json())
            .then(data => {
                const userTable = document.getElementById('userTable');
                userTable.innerHTML = '';
                data.users.forEach(user => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td><input type="checkbox" name="user_ids" value="${user.user_id}"></td>
                        <td>${user.user_id}</td>
                        <td>${user.email}</td>
                        <td>${user.roles}</td>
                    `;
                    userTable.appendChild(row);
                });

                // Enable/disable pagination buttons
                document.getElementById('prevPage').parentElement.classList.toggle('disabled', page === 1);
                document.getElementById('nextPage').parentElement.classList.toggle('disabled', data.users.length < perPage);
            });
    }

    document.getElementById('searchInput').addEventListener('input', function() {
        const filter = this.value.toLowerCase();
        const rows = document.querySelectorAll('#userTable tr');
        rows.forEach(row => {
            const username = row.cells[2].textContent.toLowerCase();
            const email = row.cells[3].textContent.toLowerCase();
            if (username.includes(filter) || email.includes(filter)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });

    document.getElementById('selectAll').addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('#userTable input[type="checkbox"]');
        checkboxes.forEach(checkbox => checkbox.checked = this.checked);
    });

    document.getElementById('prevPage').addEventListener('click', function(event) {
        event.preventDefault();
        if (currentPage > 1) {
            currentPage--;
            fetchUsers(currentPage);
        }
    });

    document.getElementById('nextPage').addEventListener('click', function(event) {
        event.preventDefault();
        currentPage++;
        fetchUsers(currentPage);
    });

    // Initial fetch
    fetchUsers(currentPage);
});