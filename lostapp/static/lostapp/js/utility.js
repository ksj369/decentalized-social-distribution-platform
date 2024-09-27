'use strict';

async function getHost(authorId) {
    return fetch(`${window.location.origin}/api/authors/${authorId}/`)
        .then(response => response.json())
        .then(data => {
            let host = data.host;
            if (!host.endsWith("/")) {
                host += "/";
            }
            host += "api/";
            console.log(host);
            return host;
        })
        .catch(error => {
            console.error('Error fetching data:', error);
        });
}

async function inboxPost(receiver, itemData) {
    // Function for posting to inbox. Accepts Author json as receiver and itemData for item to post
    // to given Author's inbox. Returns response of inbox request.
    var receiverId = receiver.url.split("/").slice(-1)[0];
    var receiverHost = await getHost(receiverId);
    var receiverInbox = `${receiverHost}authors/${receiverId}/inbox/`;
    const csrftoken = document.querySelector('[name=csrf-token]').content; // Get the CSRF token from the meta tag

    return fetch(receiverInbox, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify(itemData),
        credentials: 'same-origin'
    })
        .then(response => {
            if (response.status == 201) {
                console.log(itemData);
                console.log('Item posted successfully.');
            }
            return response;
        })
        .catch(error => console.error('Error posting item:', error));
}