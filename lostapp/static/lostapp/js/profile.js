"use strict";

// getHost and inboxPost are in utility.js

var homeUrl = "";
var requestOpts = {}

document.addEventListener("DOMContentLoaded", async function () {
    const currentURL = window.location.href;
    const authorId = currentURL.split('/').slice(-2, -1)[0];
    const loggedInAuthorId = document.getElementById("user").dataset.loggedInAuthorId;

    homeUrl = await getHost(authorId);

    // fetchFollowStatus(authorId, userUrl);
    fetchFollowStatus(authorId, loggedInAuthorId);
    profileInfo(authorId, loggedInAuthorId);
    allPosts(authorId, loggedInAuthorId);


    document.querySelectorAll('.follow-button').forEach(function (button) {
        // button.addEventListener('click', function () {
        //     const action = this.dataset.action;
        //
        //     // if (action === 'follow') {
        //     //     followAuthor(authorId);
        //     // } else if (action === 'unfollow') {
        //     //     unfollowAuthor(authorId);
        //     // }
        // });
    });
});



function fetchFollowStatus(authorId, userId) {
    console.log(userUrl.split('/').slice(-1)[0]);
        console.log("here:",userId,authorId);
        fetch(`${homeUrl}authors/${authorId}/check_follow_status/${userId}`, requestOpts)
            .then(response => {
                const followButton = document.querySelector('.follow-button[data-author-id="' + authorId + '"]');
                const unfollowButton = followButton.nextElementSibling; // Get the next button (unfollow button)
                console.log(response.status);
                if (authorId==userId){
                    followButton.style.display = 'none'; // Hide the follow button if not following
                    unfollowButton.style.display = 'none'; // Hide the unfollow button
                }
                else{
                    if (response.status === 202) {
                        followButton.style.display = 'block'; // Show the follow button if not following
                        unfollowButton.style.display = 'none'; // Hide the unfollow button
                    } else {
                        followButton.style.display = 'none'; // Hide the follow button if already following
                        unfollowButton.style.display = 'block'; // Show the unfollow button
                    }
            }
            }).catch(function (error) {
            console.error('Fetch error:', error);
            alert('Error: ' + error.message);
        });
}






async function follow(authorId, followerId) {
    // console.log(followerId);
    // const followerIdEncoded = encodeURIComponent(followerId);
    // console.log(followerIdEncoded);
    // fetch(`/api/authors/${authorId}/followers/${followerIdEncoded}`, {
    //     method: 'PUT',
    //     headers: {
    //         'Content-Type': 'application/json',
    //         'X-CSRFToken': getCookie('csrftoken')
    //     }
    // }).then(response => {
    //     if (response.ok) {
    // document.querySelector('.follow-button[data-author-id="' + authorId + '"]').style.display = 'none';
    // location.reload();
    // Hide the follow button
    const followButton = document.querySelector('.follow-button[data-author-id="' + authorId + '"]');
    followButton.style.display = 'none';

    // Show the pending button
    const pendingButton = document.querySelector('.pending-button[data-author-id="' + authorId + '"]');

    pendingButton.style.display = 'block';
    console.log("hello")
    console.log(followerId);
    console.log(followerId.split('/').slice(-1)[0]);

    var sender = await getAuthor(followerId.split('/').slice(-1)[0]);
    var author = await getAuthor(authorId);

    console.log(author)
    console.log(sender)
    var followData = {
        type: "Follow",
        summary: `${sender.displayName} wants to follow ${author.displayName}`,
        actor: sender,
        object: author,
    }
    var res = await inboxPost(author, followData);

    console.log("Follow request sent", followData);

    var inbox = await getInbox(authorId);
    console.log(inbox);
    // }
    // }).catch(error => {
    //     console.error('Error:', error);
    // });
}



function unfollow(authorId, userId) {
    console.log(userId.split('/').slice(-1)[0]);
    fetch(`${homeUrl}authors/${userId.split('/').slice(-1)[0]}/followers/${authorId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    }).then(response => {
        if (response.ok) {
            // document.querySelector('.follow-button[data-author-id="' + authorId + '"]').style.display = 'block';
            location.reload();
        }
    }).catch(error => {
        console.error('Error:', error);
    });

}

// Function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function profileInfo(authorId, loggedInAuthorId) {
    fetch(`${homeUrl}authors/${authorId}`, requestOpts)
        .then(response => response.json())
        .then(data => {
            const profileContainer = document.getElementById('profile');
            const profileInfo = document.createElement('div');
            profileInfo.innerHTML = `
                    <div class="profile_image">
                        <img src="${data.profileImage}" alt="Profile Picture" style="max-width: 10em; max-height: 10em"/>
                    </div>
                    <h3 class="title is-4">${data.displayName}</h3>
                    <p>Github: <a href="${data.github}">${data.github}</a></p>
                    <p>Host: <a href="${data.host}">${data.host}</a></p>
                `;
            if (authorId === loggedInAuthorId) {
                const editProfileButton = document.createElement('button');
                editProfileButton.classList.add('button', 'is-primary', "is-outlined", "is-rounded", "is-small", "is-light");
                editProfileButton.style.marginTop = '1em';
                editProfileButton.textContent = 'Edit Profile';
                editProfileButton.addEventListener('click', () => {
                    window.location.href = `/edit_profile/`;
                });
                profileInfo.appendChild(editProfileButton);
            }
            profileContainer.appendChild(profileInfo);
        })
        .catch(error => {
            console.error('Error fetching data:', error);
        });
}

async function getAuthor(authorId) {
    var host = await getHost(authorId);
    return fetch(`${host}authors/${authorId}`)
        .then(response => response.json())
        .catch(error => { console.error('Error fetching author data:', error); })
}

async function isFollower(authorId, otherId) {
    var host = await getHost(authorId);
    var otherAuthor = await getAuthor(otherId);
    return fetch(`${host}authors/${authorId}/followers/${encodeURIComponent(otherAuthor.id)}`)
        .then(response => {
            if (response.status == 404) {
                return false;
            } else if (response.status == 200) {
                return true;
            }
        })
        .catch(error => {
            console.error('Error fetching follower data:', error);
        })
}

async function isFriend(authorId, otherId) {
    var follows = await isFollower(authorId, otherId);
    var following = await isFollower(otherId, authorId);
    return follows && following;
}

async function filterPosts(posts, authorId, loggedInAuthorId) {
    if (authorId != loggedInAuthorId) {
        var is_friend = await isFriend(authorId, loggedInAuthorId);
        var filteredPosts = [];
        for (var post of posts) {
            if (post.visibility == "PUBLIC") {
                filteredPosts.push(post);
            } else if (post.visibility == "FRIENDS" && is_friend) {
                filteredPosts.push(post);
            }
        }
        return filteredPosts;
    } else {
        return posts;
    }
}

async function allPosts(authorId, loggedInAuthorId) {
    fetch(`${homeUrl}authors/${authorId}/posts`, requestOpts)
        .then(response => response.json())
        .then(async data => {
            console.log(data);
            var filteredPosts = await filterPosts(data, authorId, loggedInAuthorId);
            const postsSection = document.getElementById('posts');
            const postsList = document.createElement('ul');
            if (filteredPosts.length === 0) {
                postsList.innerHTML = `
                        <hr></hr>
                        <p>No posts are visible.</p>
                    `;
            } else {
                postsList.innerHTML = `
                        <hr></hr>
                        <h2 class="title is-4">Posts</h2>
                    `;
            }
            filteredPosts.forEach(post => {
                const postItem = document.createElement('li');
                const boxDiv = document.createElement('div');
                boxDiv.classList.add('box');
                boxDiv.style.marginBottom = '1em';
                if (post.contentType === 'text/plain') {
                    boxDiv.innerHTML = `
                            <h1><b>${post.author.displayName}</b></h1>
                            <h3><a href="${post.id}">${post.title}</a></h3>
                            <p>${new Date(post.published).toLocaleString()}</p>
                            <p>${post.content}</p>
                        `;
                } else if (post.contentType === 'text/markdown') {
                    boxDiv.innerHTML = `
                            <h1><b>${post.author.displayName}</b></h1>
                            <h3><a href="${post.id}">${post.title}</a></h3>
                            <p>${new Date(post.published).toLocaleString()}</p>
                            <p>${marked.parse(post.content)}</p>
                        `;
                } else {
                    boxDiv.innerHTML = `
                            <h1><b>${post.author.displayName}</b></h1>
                            <h3><a href="${post.id}">${post.title}</a></h3>
                            <p>${new Date(post.published).toLocaleString()}</p>
                            <img src="${post.content}" alt="Post Image" style="max-width: 500px; max-height: 400px">
                            <br></br>
                        `;
                }
                if (authorId === loggedInAuthorId) {
                    const editButton = document.createElement('button');
                    editButton.classList.add('button', 'is-primary', "is-small", "is-light");
                    editButton.textContent = 'Edit';
                    editButton.addEventListener('click', () => {
                        window.location.href = `${post.id}/edit`;
                    });
                    boxDiv.appendChild(editButton);
                }
                postItem.appendChild(boxDiv);
                postsList.appendChild(postItem);
            });
            postsSection.appendChild(postsList);
        })
        .catch(error => {
            console.error('Error fetching data:', error);
        });
}

async function getInbox(authorId) {
    return fetch(`${homeUrl}authors/${authorId}/inbox`)
        .then(response => response.json())
        .catch(error => {
            console.error('Error fetching data:', error);
        });
}
