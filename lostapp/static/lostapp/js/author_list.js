'use strict';

document.addEventListener('DOMContentLoaded', function () {
    const profileContainer = document.getElementById('profile');

    fetch('/api/authors/')
        .then(response => response.json())
        .then(data => {
            var authors = data.items;
            authors.forEach(profile => {
                const authorId = profile.id.split('/').slice(-1);
                const profileCard = document.createElement('div');
                profileCard.className = 'block';
                profileCard.innerHTML = `
                    <div class="card">
                        <a href="${window.location.origin}/authors/${authorId}">
                            <div class="card-content">
                                <div class="media">
                                    <div class="media-left">
                                        <figure class="image is-48x48">
                                            <img src="${profile.profileImage}" alt="Placeholder image">
                                        </figure>
                                    </div>
                                    <div class="media-content">
                                        <p class="title is-4">
                                            ${profile.displayName}
                                        </p>
                                        <p class="subtitle is-7">
                                            @${profile.host}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </a>
                    </div>
                `;
                profileContainer.appendChild(profileCard);
            });
        });
});