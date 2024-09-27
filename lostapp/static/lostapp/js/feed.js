'use strict';

// getHost is in utility.js
var homeUrl = "";

document.addEventListener('DOMContentLoaded', async function () {
    const currentURL = window.location.href;
    const authorId = document.getElementById("user").dataset.loggedInAuthorId;

    // authorId is empty if user is not logged in.
    if (authorId){
        homeUrl = await getHost(authorId);
    }

    fillFeed(authorId);

    const followRequestList = document.getElementById('follow-request-list');
    if (followRequestList) {
        fettchpendingrequests();
    }

    });

async function getInbox(authorId){
    return fetch(`${homeUrl}authors/${authorId}/inbox`)
    .then(response => response.json())
    .catch(error => {
    console.error('Error fetching data:', error);
    });
}

async function getAllPosts(){
    return fetch(`${window.location.origin}/api/authors/posts/all`)
    .then(response => response.json())
    .catch(error => {
    console.error('Error fetching data:', error);
    });
}

async function fillFeed(authorId){
    var all = await getAllPosts();
    if (authorId){
        var inbox = await getInbox(authorId);
        all = all.concat(inbox.items);        
    }

    const dataContainer = document.getElementById('main-stream');
    all.forEach(item => {
        const listItem = document.createElement('li');
        const boxDiv = document.createElement('div');
        boxDiv.classList.add('box');
        listItem.classList.add('feed-item');
        
        if (item.type == "post"){
            if (item.contentType === 'text/markdown') {
                boxDiv.innerHTML = `
                    <a class="author-name" href="${item.author.id}">${item.author.displayName}</a>
                    <div>
                    <a class="post-title" href="${item.source}">${item.title}</a>
                    <div class="post-content">${marked.parse(item.content)}</div>
                `;
            } else if (item.contentType === 'text/plain') {
                boxDiv.innerHTML = `
                    <a class="author-name" href="${item.author.id}">${item.author.displayName}</a>
                    <div>
                    <a class="post-title" href="${item.source}">${item.title}</a>
                    <p class="post-content">${item.content}</p>
                `;
            } else if (item.contentType === 'image/png' || item.contentType === 'image/jpeg') {
                boxDiv.innerHTML = `
                    <a class="author-name" href="${item.author.id}">${item.author.displayName}</a>
                    <div>
                    <a class="post-title" href="${item.source}">${item.title}</a>
                    <div>
                    <img class="post-image" src="${item.content}" alt="Image Post">
                `;
            }
        } else if (item.type == "comment"){
            var postLink = item.id.split("/").slice(0, -2).join('/')
            boxDiv.innerHTML = `
            <a class="author-name" href="${item.author.id}">${item.author.displayName}</a> commented
            "${item.comment}" on <a href="${postLink}">your post.</a>
            `
        } else if (item.type == "Like"){
            boxDiv.innerHTML = `
            <a class="author-name" href="${item.author.id}">${item.author.displayName}</a> liked <a href="${item.object}">your post.</a>
            `
        }
 
        listItem.appendChild(boxDiv);
        listItem.innerHTML += '<hr></hr>';
        document.querySelector('.post-list').appendChild(listItem);
    });
}


    function fettchpendingrequests() {
        // Fetch pending follow requests asynchronously
    fetch('/api/authors/pending_follow_requests/' )
    .then(response => response.json())
    .then(data => {
        const followRequestList = document.getElementById('follow-request-list');

        // Clear any existing content in the list
        followRequestList.innerHTML = '';

        // Populate the list with pending follow requests
        console.log(data)
        console.log(typeof data)
        if (Object.keys(data).length > 0) {
            Object.values(data).forEach(followRequest => {
                const listItem = document.createElement('li');
                listItem.textContent = `Follow request from ${followRequest.displayName}`;
                
                // Create accept button
                const acceptButton = document.createElement('button');
                acceptButton.textContent = 'Accept';
                acceptButton.classList.add('button', 'is-success', 'request-button');
                acceptButton.dataset.authorId = followRequest.authorId; // Set authorId
                acceptButton.dataset.followerId = followRequest.actor; // Set followerId
                acceptButton.dataset.action = 'accept';
                acceptButton.addEventListener('click', handleRequestAction);
                listItem.appendChild(acceptButton);

                // Create decline button
                const declineButton = document.createElement('button');
                declineButton.textContent = 'Decline';
                declineButton.classList.add('button', 'is-danger', 'request-button');
                declineButton.dataset.authorId = followRequest.authorId; // Set authorId
                declineButton.dataset.followerId = followRequest.actor; // Set followerId
                declineButton.dataset.action = 'decline';
                declineButton.addEventListener('click', handleRequestAction);
                listItem.appendChild(declineButton);

                followRequestList.appendChild(listItem);
            });
        } else {
            // No pending follow requests
            const listItem = document.createElement('li');
            listItem.textContent = 'No follow requests.';
            followRequestList.appendChild(listItem);
        }
    })
    .catch(error => {
        console.error('Error fetching follow requests:', error);
    });

    }




        
    function accept_request(authorId, followerId) {
        console.log(followerId);
        const followerIdEncoded = encodeURIComponent(followerId);
        console.log(followerIdEncoded);
        fetch(`/api/authors/${authorId}/request/${encodeURIComponent(followerId)}`, {
            method: 'PUT',
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


    function decline_request(authorId, followerId) {
        console.log("foloower id",followerId);
        console.log("author id",authorId);
        const followerIdEncoded = encodeURIComponent(followerId);
        // console.log(followerIdEncoded);
        fetch(`/api/authors/${authorId}/request/${encodeURIComponent(followerId)}`, {
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


    function handleRequestAction(event) {
        const authorId = event.target.dataset.authorId;
        const followerId = event.target.dataset.followerId;
        const action = event.target.dataset.action;
    
        if (action === 'accept') {
            accept_request(authorId, followerId);
        } else if (action === 'decline') {
            decline_request(authorId, followerId);
        }
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

