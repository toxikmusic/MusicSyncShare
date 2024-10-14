document.addEventListener('DOMContentLoaded', function() {
    const songFeed = document.getElementById('song-feed');

    function fetchSongs() {
        fetch('/api/songs')
            .then(response => response.json())
            .then(songs => {
                songFeed.innerHTML = '';
                songs.forEach(song => {
                    const songElement = createSongElement(song);
                    songFeed.appendChild(songElement);
                });
            })
            .catch(error => console.error('Error fetching songs:', error));
    }

    function createSongElement(song) {
        const col = document.createElement('div');
        col.className = 'col-md-6 col-lg-4 mb-4';

        const card = document.createElement('div');
        card.className = 'card h-100';

        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';

        const title = document.createElement('h5');
        title.className = 'card-title';
        title.textContent = song.title;

        const artist = document.createElement('p');
        artist.className = 'card-text';
        artist.textContent = `Artist: ${song.artist}`;

        const uploadDate = document.createElement('p');
        uploadDate.className = 'card-text';
        uploadDate.textContent = `Uploaded: ${song.upload_date}`;

        const playButton = document.createElement('a');
        playButton.href = song.url;
        playButton.className = 'btn btn-primary';
        playButton.textContent = 'Play';
        playButton.target = '_blank';

        cardBody.appendChild(title);
        cardBody.appendChild(artist);
        cardBody.appendChild(uploadDate);
        cardBody.appendChild(playButton);

        card.appendChild(cardBody);
        col.appendChild(card);

        return col;
    }

    // Initial fetch
    fetchSongs();

    // Auto-update every 5 minutes
    setInterval(fetchSongs, 5 * 60 * 1000);
});
