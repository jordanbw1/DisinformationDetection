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

                    const checkboxCell = document.createElement('td');
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.name = 'user_ids';
                    checkbox.value = user.user_id;
                    checkboxCell.appendChild(checkbox);
                    row.appendChild(checkboxCell);

                    const userIdCell = document.createElement('td');
                    userIdCell.textContent = user.user_id;
                    row.appendChild(userIdCell);

                    const emailCell = document.createElement('td');
                    emailCell.textContent = user.email;
                    row.appendChild(emailCell);

                    const rolesCell = document.createElement('td');
                    rolesCell.textContent = user.roles;
                    row.appendChild(rolesCell);

                    userTable.appendChild(row);
                });

                // Enable/disable pagination buttons
                document.getElementById('prevPage').parentElement.classList.toggle('disabled', page === 1);
                document.getElementById('nextPage').parentElement.classList.toggle('disabled', data.users.length < perPage);
            });
    }

    function showMessage(message, category) {
        const jsMessages = document.getElementById('js-messages');
        const alert = document.createElement('div');
        alert.className = `alert alert-dismissible flash flash-${category}`;
        alert.innerHTML = `
            <button type="button" class="close" data-dismiss="alert">&times;</button>
            ${message}
        `;
        jsMessages.appendChild(alert);
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

    document.getElementById('actionSelect').addEventListener('change', function() {
        const actionSelect = document.getElementById('actionSelect');
        const roleSelectDiv = document.getElementById('roleSelectDiv');
        const actionSubmitButton = document.getElementById('actionSubmitButton');
        if (actionSelect.value === 'add_role' || actionSelect.value === 'remove_role') {
            roleSelectDiv.hidden = false;
            actionSubmitButton.hidden = false;
        } else {
            roleSelectDiv.hidden = true;
            actionSubmitButton.hidden = true;
        }
    });

    function submitUserForm(formData) {
        // Append the CSRF token to the FormData if not already included
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;
        if (!formData.has('csrf_token')) {
            formData.append('csrf_token', csrfToken);
        }

        // Handle form submission
        fetch('/admin/actions', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status !== 200) {
                throw new Error(body.error || 'Unknown error');
            }
            // Show success message
            showMessage(body.message || 'Action executed successfully.', 'success');
            // Reload the user table
            fetchUsers(currentPage);
        })
        .catch(error => {
            // Display error message
            showMessage(error.message || 'An error occurred while executing the action.', 'error');
        });
    }

    document.getElementById('userForm').addEventListener('submit', function(event) {
        const actionSelect = document.getElementById('actionSelect');
        const roleInput = document.getElementById('roleSelect');
        const selectedRows = document.querySelectorAll('#userTable input[type="checkbox"]:checked');
        // If no rows are selected, show an error message
        if (selectedRows.length === 0) {
            event.preventDefault();
            showMessage('Please select at least one user.', 'error');
        // If the action is not selected or the role is not entered, show an error message
        } else if (!actionSelect.value || !roleInput.value || actionSelect.value == 'none' || roleInput.value == 'none') {
            event.preventDefault();
            showMessage('Please select an action and a role.', 'error');
        } else {
            if (roleInput.value === 'admin') {
                // Prevent the form from submitting immediately
                event.preventDefault();
                formToSubmit = this;
                // Set the warning message based on if this is an add or remove action
                const action = actionSelect.value === 'add_role' ? 'add' : 'remove';
                document.getElementById('ModalWarningText').textContent = `Are you sure you want to ${action} the admin role for the selected users?`;
                $('#warningModal').modal('show');
                return;
            }
            event.preventDefault();
            const formData = new FormData(this);
            submitUserForm(formData);
        }
    });

    // Modal confirm button
    document.getElementById('modalConfirmButton').addEventListener('click', function() {
        if (formToSubmit) {
            const formData = new FormData(formToSubmit);
            submitUserForm(formData);
        }
        $('#warningModal').modal('hide');
    });

    // Initial fetch
    fetchUsers(currentPage);
});