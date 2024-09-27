'use strict';

document.addEventListener("DOMContentLoaded", function () {
    const currentURL = window.location.href;
    const authorId = currentURL.split('/').slice(4, 5);
    const postId = currentURL.split('/').slice(6, 7);

    prefillEdit(authorId, postId);
    const edit_button = document.getElementById('edit-button');
    edit_button.addEventListener("click", () => editPost(authorId, postId));

    var image_input = document.getElementById('image_file')
    image_input.addEventListener("change", () => {
        console.log("file selected");
        var reader = new FileReader();
        reader.readAsDataURL(image_input.files[0]);
        reader.onload = function () {
            console.log(reader.result);
            var content_elem = document.getElementById('edit-content');
            content_elem.innerHTML = reader.result;
          };
        }

    )
    
    function prefillEdit(authorId, postId) {
        fetch(`/api/authors/${authorId}/posts/${postId}`)
            .then(response => response.json())
            .then(data => {
                const title_elem = document.getElementById('edit-title');
                const content_elem = document.getElementById('edit-content');
                title_elem.value = data.title;
                content_elem.innerHTML = data.content;

                // Remove image button and label for text/markdown posts.
                if (data.contentType !== 'image/png') {
                    const image_button = document.getElementById('image_file');
                    image_button.remove();
                    document.querySelector(`label[for="image_file"]`).remove();
                }

            }).catch(error => {
            console.error('Error fetching data:', error);
        });
    }
});


function editPost(authorId, postId) {
    const url = `/api/authors/${authorId}/posts/${postId}/`; // Adjust the URL based on your routing
    const postUrl = `/authors/${authorId}/posts/${postId}/`;
    const csrftoken = document.querySelector('[name=csrf-token]').content; // Get the CSRF token from the meta tag
    const title = document.getElementById('edit-title').value
    const content = document.getElementById('edit-content').value
    console.log(title, content)

    fetch(url, {
        method: 'PUT',
        headers: {
            'X-CSRFToken': csrftoken, // Include the CSRF token in the request header
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            "title": document.getElementById('edit-title').value,
            "content": document.getElementById('edit-content').value,
        }),
    }).then(response => {
        if (response.status === 303) {
            // Handle success response
            alert('Item updated successfully');
            // redirect to the returned url
            window.location.href = postUrl;
        } else {
            // Handle error response
            alert('Error updating item');
        }
    }).catch(error => console.error('Error:', error));
}
