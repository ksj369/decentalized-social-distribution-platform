'use strict';

// getHost and inboxPost are in utility.js

var homeUrl = "";
var requestOpts = {}

document.addEventListener("DOMContentLoaded", async function () {
    const currentURL = window.location.href;
    const authorId = currentURL.split('/').slice(4, 5)[0];
    const viewingAuthorId = document.getElementById('viewing_author').innerHTML;
    const postId = currentURL.split('/').slice(6, 7)[0];

    homeUrl = await getHost(authorId);

    fillPost(authorId, postId);
    async function fillPost(authorId, postId){
        const postData = await getPost(authorId, postId);

        // Title
        var title = document.getElementById('post_title');
        title.innerHTML = postData.title;
        
        // Content
        var content = document.getElementById('content');
        if (postData.contentType == 'text/plain'){
            content.innerHTML = postData.content;
        }
        else if (postData.contentType == 'text/markdown'){
            content.innerHTML = marked.parse(postData.content);
        }
        else{
            var img_src = `${homeUrl}authors/${authorId}/posts/${postId}/image/`
            content.innerHTML = `<img src=${img_src} alt='Post Image'></img>`
            var imageLinkButton = document.getElementById('image_link');
            imageLinkButton.removeAttribute("hidden");
            imageLinkButton.addEventListener("click", () => {navigator.clipboard.writeText(img_src); 
                    alert('Copied link');});

        }

        // Set button visibility according to identity of viewing author and set results of button clicks.
        var editPostButton = document.getElementById('edit_post');
        var deleteButton = document.getElementById('delete_post');
        var shareButton = document.getElementById('share_post_with_followers');
        var likeButton = document.getElementById('like_post');

        if (viewingAuthorId == authorId){
            editPostButton.removeAttribute("hidden");
            deleteButton.removeAttribute("hidden");
            editPostButton.addEventListener("click", () => {window.location.href = `${window.location.origin}/authors/${authorId}/posts/${postId}/edit/`})
            deleteButton.addEventListener("click", () => deletePost(authorId, postId));
        } else if (viewingAuthorId != authorId) {
            likeButton.removeAttribute("hidden")
            likeButton.addEventListener("click", () => likePost(authorId, postId));
            
            if (postData.visibility == 'PUBLIC'){
                shareButton.removeAttribute("hidden");
                shareButton.addEventListener("click", () => sharePost(viewingAuthorId));
            } 
        }

        // Post Likes.
        var postLikes = await getPostLikes(authorId, postId);
        var numLikes = postLikes.length;
        var postLikeSpan = document.getElementById('post_like_count');
        if (numLikes == 1){
            postLikeSpan.innerHTML = "1 person liked this post";
        } else {
            postLikeSpan.innerHTML = `${numLikes} people liked this post`;
        }

        // Comments
        var commentButton = document.getElementById('submit_comment');
        commentButton.addEventListener("click", () => postComment(authorId, viewingAuthorId, postId))

        var commentSection = document.getElementById('comments_section');
        var comments = await getComments(authorId, postId);
        for (var comment of comments.comments){
            let commentId = comment.id.split("/").slice(-1)[0];
            var commentDivTag = document.createElement('div');
            commentDivTag.classList.add("comment")
            commentSection.appendChild(commentDivTag);

            var commentPTag = document.createElement('p');
            commentPTag.innerHTML = `Comment by ${comment.author.displayName}: ${comment.comment}`;
            commentDivTag.appendChild(commentPTag);

            var likeCommentButton = document.createElement('button');
            likeCommentButton.classList.add("like_comment");
            likeCommentButton.innerHTML = "Like Comment";
            likeCommentButton.onclick = function() {likeComment(authorId, postId, commentId)};
            commentDivTag.appendChild(likeCommentButton);
            
            var commentLikeCountSpan = document.createElement('span');
            commentLikeCountSpan.classList.add("comment_like_count");
            var commentLikes = await getCommentLikes(authorId, postId, commentId);
            var numCommentLikes = commentLikes.length;
            if (numCommentLikes == 1){
                commentLikeCountSpan.innerHTML = " 1 person liked this comment";
            } else {
                commentLikeCountSpan.innerHTML = ` ${numCommentLikes} people liked this comment`;
            }        
            commentDivTag.appendChild(commentLikeCountSpan);

            commentDivTag.appendChild(document.createElement('br'));
            commentDivTag.appendChild(document.createElement('br'));
        }

    }
});

async function postComment(authorId, viewingAuthorId, postId){
    const csrftoken = document.querySelector('[name=csrf-token]').content; // Get the CSRF token from the meta tag
    var commentContent = document.getElementById('comment_content').value;

    // Check if the comment content is empty
    if (commentContent.trim() === '') {
        console.log("No text");
        return;
    }

    var commentData = {
        post: postId,
        author: authorId,
        comment: commentContent,
        contentType: "text/markdown",
    }

    fetch(`${homeUrl}authors/${authorId}/posts/${postId}/comments/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify(commentData),
        credentials: 'same-origin'
    })
        .then(response => {
            if (response.status == 201) {
                console.log('Commented successfully.');
                return response.json()
            }
        })
        .then(async commentData => {
            // Send new comment to post creator's inbox.
            var postAuthor = await getAuthor(authorId);
            var res = await inboxPost(postAuthor, commentData);
            location.reload()
        })
        .catch(error => console.error('Error posting item:', error));      
}

async function getAuthor(authorId){
    return fetch(`${homeUrl}authors/${authorId}/`, requestOpts)
    .then(response => response.json())
    .catch(error => {
    console.error('Error fetching data:', error);
    });
}

async function getPost(authorId, postId){
    console.log(`${homeUrl}`)
    return fetch(`${homeUrl}authors/${authorId}/posts/${postId}`, requestOpts)
    .then(response => response.json())
    .catch(error => {
    console.error('Error fetching data:', error);
    });
}

async function getPostLikes(authorId, postId){
    return fetch(`${homeUrl}authors/${authorId}/posts/${postId}/likes`)
    .then(response => response.json())
    .catch(error => {
    console.error('Error fetching data:', error);
    });
}

async function getCommentLikes(authorId, postId, commentId){
    return fetch(`${homeUrl}authors/${authorId}/posts/${postId}/comments/${commentId}/likes`)
    .then(response => response.json())
    .catch(error => {
    console.error('Error fetching data:', error);
    });
}

async function getComments(authorId, postId){
    return fetch(`${homeUrl}authors/${authorId}/posts/${postId}/comments/`)
    .then(response => response.json())
    .catch(error => {
    console.error('Error fetching data:', error);
    });
}

async function sharePost(authorId){
    var currentURL = window.location.href;
    var postAuthorId = currentURL.split('/').slice(4, 5);
    var postId = currentURL.split('/').slice(6, 7);

    // Get post data and update source.
    var postData = await getPost(postAuthorId, postId);
    postData.source = currentURL;

    // Fetch followers of given author.
    fetch(`${homeUrl}authors/${authorId}/followers/`)
    .then(response => response.json())
    .then(async data => {
        const followers = data.items;
        // Loop through followers and share the post to their inbox.
        for (var follower of followers){
            let res = await inboxPost(follower, postData);      
        }    

    }).catch(error => {console.error('Error fetching follower data:', error);})
}

function deletePost(authorId, postId) {
    const url = `${homeUrl}authors/${authorId}/posts/${postId}/`; // Adjust the URL based on your routing
    const csrftoken = document.querySelector('[name=csrf-token]').content; // Get the CSRF token from the meta tag
    fetch(url, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrftoken, // Include the CSRF token in the request header
        },
    })
        .then(response => {
            if (response.status === 204) {
                // Handle success response
                alert('Item deleted successfully');
                // redirect to the returned url
                window.location.href = '/';
            }
        })
        .catch(error => console.error('Error:', error));
}

async function likePost(authorId, postId) {
    const url = `${homeUrl}authors/${authorId}/posts/${postId}/likes/`;
    const csrftoken = document.querySelector('[name=csrf-token]').content;
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken, // Include the CSRF token in the request header
        },
    })
        .then(response => {
            if (response.status == 201) {
                alert('Post liked successfully');
                return response.json();
            }
        })
        .then(async data => {
            // Send Like to Post Author's Inbox
            const currentURL = window.location.href;
            const postAuthorId = currentURL.split('/').slice(4, 5);
            var postAuthor = await getAuthor(postAuthorId);
            var likeData = data.like;
            var res = await inboxPost(postAuthor, likeData);
            location.reload();
        })
        .catch(error => console.error('Error:', error));
}

function likeComment(authorId, postId, commentId) {
    const url = `authors/${authorId}/posts/${postId}/comments/${commentId}/likes/`;
    const csrftoken = document.querySelector('[name=csrf-token]').content;
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
        },
    })
        .then(response => {
            if (response.status == 201) {
                alert('Comment liked successfully');
                location.reload();
                return response.json();
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}
