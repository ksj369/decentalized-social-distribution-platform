'use strict';

// inboxPost is in utility.js

document.addEventListener("DOMContentLoaded", async function () {
    const contentArea = document.getElementById('content');
    const contentTitle = document.getElementById('content-title');
    const contentFormatSelect = document.getElementById('content-format');

    contentFormatSelect.addEventListener('change', function () {
        const selectedOption = contentFormatSelect.value;
        const uploadButton = document.querySelector('.file');

        if (selectedOption === 'image/png') {
            uploadButton.style.display = 'block';
            contentArea.style.display = 'none';
            contentTitle.style.display = 'none';
        } else {
            uploadButton.style.display = 'none';
            contentArea.style.display = 'block';
            contentTitle.style.display = 'block';
        }
    });
});

function showFileName(input) {
    const fileName = input.files[0].name;
    const fileLabel = document.querySelector('.file-name');
    fileLabel.textContent = fileName;
}

function createPost() {
    const currentURL = window.location.href;
    const urlParts = currentURL.split('/');
    const authorId = urlParts[urlParts.length - 4];
    const homeUrl = "/";
    const url = `/api/authors/${authorId}/posts/`;
    const title = document.getElementById('title').value;
    const description = document.getElementById('description').value;
    const contentFormat = document.getElementById('content-format').value;
    const visibility = document.getElementById('visibility').value;
    const csrftoken = document.querySelector('[name=csrf-token]').content;
    let jsonData = {
        type: 'post',
        title: title,
        description: description,
        content: "",
        contentType: contentFormat,
        visibility: visibility,
    };
    if (contentFormat === 'image/png' || contentFormat === 'image/jpeg') {
        const fileInput = document.getElementById('image_file');
        const file = fileInput.files[0];
        const reader = new FileReader();
        reader.onloadend = function () {
            const base64Prefix = `data:image/${contentFormat.split('/')[1]};base64,`;
            jsonData.content = base64Prefix + reader.result.split(',')[1];
            jsonData.contentType = contentFormat;
            fetchPost(url, jsonData, csrftoken);
        };
        reader.readAsDataURL(file);
    } else {
        const content = document.getElementById('content').value;
        jsonData.content = content;
        fetchPost(url, jsonData, csrftoken);
    }
}

function fetchPost(url, jsonData, csrftoken) {
    const homeUrl = "/";
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify(jsonData),
        credentials: 'same-origin'
    })
        .then(response => {
            if (response.status === 201) {
                return response.json();
            }
        })
        .then(postData => {
            if (postData.visibility != "UNLISTED") {
                // Fetch followers of author.
                const currentURL = window.location.href;
                const urlParts = currentURL.split('/');
                const authorId = urlParts[urlParts.length - 4];
                fetch(`${window.location.origin}/api/authors/${authorId}/followers/`)
                    .then(response => response.json())
                    .then(async data => {
                        const followers = data.items;
                        // Loop through followers and share the post to their inbox.
                        for (var follower of followers) {
                            console.log("wd")
                            // Post all public posts.
                            if (postData.visibility == "PUBLIC") {
                                console.log(postData.visibility);
                                let res = await inboxPost(follower, postData);
                            } else {
                                // Only friends get friends only posts. We just need to check if the author
                                // follows the follower back.
                                let followerId = follower.id.split("/").slice(-1);
                                if (isFollower(followerId, authorId)) {
                                    let res = await inboxPost(follower, postData);
                                }
                            }
                        }
                    }).catch(error => { console.error('Error fetching follower data:', error); })
            }
            window.location.href = homeUrl;
        })
        .catch(error => {
            console.error('Error:', error);
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