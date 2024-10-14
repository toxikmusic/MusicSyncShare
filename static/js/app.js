document.addEventListener('DOMContentLoaded', function() {
    const songFeed = document.getElementById('song-feed');
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');

    function fetchSongs() {
        fetch('/api/songs')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(songs => {
                songFeed.innerHTML = '';
                if (songs.length === 0) {
                    displayNoSongsMessage();
                } else {
                    songs.forEach(song => {
                        const songElement = createSongElement(song);
                        songFeed.appendChild(songElement);
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching songs:', error);
                displayErrorMessage();
            });
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

    function displayNoSongsMessage() {
        const message = document.createElement('div');
        message.className = 'col-12 text-center';
        message.innerHTML = '<h3 class="text-muted">No songs available at the moment.</h3>';
        songFeed.appendChild(message);
    }

    function displayErrorMessage() {
        const message = document.createElement('div');
        message.className = 'col-12 text-center';
        message.innerHTML = '<h3 class="text-danger">Error loading songs. Please try again later.</h3>';
        songFeed.appendChild(message);
    }

    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            fetchSongs();  // Refresh the song list after successful upload
            fileInput.value = '';  // Clear the file input
        })
        .catch((error) => {
            console.error('Error:', error);
            alert('Failed to upload file. Please try again.');
        });
    });

    // Initial fetch
    fetchSongs();

    // Auto-update every 5 minutes
    setInterval(fetchSongs, 5 * 60 * 1000);
});
