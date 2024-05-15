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
                    const userIdCell = document.createElement('td');
                    userIdCell.textContent = user.user_id;
                    row.appendChild(userIdCell);

                    const emailCell = document.createElement('td');
                    emailCell.textContent = user.email;
                    row.appendChild(emailCell);

                    const rolesCell = document.createElement('td');
                    rolesCell.textContent = user.roles;
                    row.appendChild(rolesCell);

                    const checkboxCell = document.createElement('td');
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.name = 'user_ids';
                    checkbox.value = user.user_id;
                    checkboxCell.appendChild(checkbox);
                    row.appendChild(checkboxCell);

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