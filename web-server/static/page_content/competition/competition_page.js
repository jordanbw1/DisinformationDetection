const comp_id = document.getElementById('comp_id').value;

document.addEventListener('DOMContentLoaded', (event) => {
    let currentPage = 1;
    const perPage = 10;

    function fetchScoreboard(page) {
        fetch(`/competition/scoreboard/${comp_id}?page=${page}&per_page=${perPage}`)
            .then(response => response.json())
            .then(data => {
                console.log("DATA:", data)
                const scoreboard = document.getElementById('scoreboard');
                scoreboard.innerHTML = '';
                data.scoreboard.forEach(score => {
                    const row = document.createElement('tr');

                    const nameCell = document.createElement('td');
                    nameCell.textContent = score.name;
                    row.appendChild(nameCell);

                    const scoreCell = document.createElement('td');
                    scoreCell.textContent = score.score;
                    row.appendChild(scoreCell);

                    const rankCell = document.createElement('td');
                    rankCell.textContent = score.rank;
                    row.appendChild(rankCell);

                    scoreboard.appendChild(row);
                });

                // Enable/disable pagination buttons
                document.getElementById('prevPage').parentElement.classList.toggle('disabled', page === 1);
                document.getElementById('nextPage').parentElement.classList.toggle('disabled', data.scoreboard.length < perPage);
            });
    }

    document.getElementById('searchInput').addEventListener('input', function() {
        const filter = this.value.toLowerCase();
        const rows = document.querySelectorAll('#scoreboard tr');
        rows.forEach(row => {
            const username = row.cells[0].textContent.toLowerCase();
            const score = row.cells[1].textContent.toLowerCase();
            const rank = row.cells[2].textContent.toLowerCase();
            if (username.includes(filter) || score.includes(filter) || rank.includes(filter) ) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });

    document.getElementById('prevPage').addEventListener('click', function(event) {
        event.preventDefault();
        if (currentPage > 1) {
            currentPage--;
            fetchScoreboard(currentPage);
        }
    });

    document.getElementById('nextPage').addEventListener('click', function(event) {
        event.preventDefault();
        currentPage++;
        fetchScoreboard(currentPage);
    });

    // Initial fetch
    fetchScoreboard(currentPage);
});