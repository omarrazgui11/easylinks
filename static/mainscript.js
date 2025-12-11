let newLinkBtn = document.getElementById('new-link-btn');
let newFolderBtn = document.getElementById('new-folder-btn');
let folders = document.getElementById('folders');
let itemsList = document.getElementById('items-list');
let directory = [0];
let currentFolderId = 0;
const changeDirectory = (folderIndex) => {
        if (directory.length === 1) {
            folders.insertBefore(backBtn, itemsList);
        }
        directory.push(folderIndex);
        currentFolder = selectCurrentFolder();
        renderItems(currentFolder);
}


const goBack = () => {
    if (directory.length > 1) {
        directory.pop();
        currentFolder = selectCurrentFolder();
        renderItems(currentFolder);
    }
    if (directory.length === 1) {
        folders.removeChild(backBtn);
    }
}
const backBtn = document.createElement('button');
backBtn.classList.add('btn', 'btn-secondary', 'mb-3', 'back-btn');
backBtn.innerText = 'Go Back';
backBtn.addEventListener('click', goBack);

const selectCurrentFolder = () => {
    // dataFolderTree is an array with the root at index 0
    let pointer = dataFolderTree[directory[0]];

    // if we are at root
    if (directory.length === 1) {
        currentFolderId = pointer.id;
        return pointer;
    }

    // walk down children using the *values* of directory, not indices into directory
    for (const idx of directory.slice(1)) {
        pointer = pointer.children[idx];
    }

    currentFolderId = pointer.id;
    return pointer;
};
let currentFolder = selectCurrentFolder();
console.log(currentFolder);
const renderItems = (currentFolder) => {
    itemsList.innerHTML = '';
    let k = 0;
    if (currentFolder.children.length === 0 && currentFolder.links.length === 0) {
        let emptyMsg = document.createElement('p');
        emptyMsg.innerText = 'This folder is empty. Add a new link or folder to get started!';
        itemsList.appendChild(emptyMsg);
    }
    for (let item of currentFolder.children) {
        let listItem = document.createElement('li');
        listItem.setAttribute('onclick', `changeDirectory(${k})`)
        listItem.innerHTML = `<strong>📁 ${item.name}</strong>`;
        threeDotsMenu = document.createElement('span');
        threeDotsMenu.classList.add('three-dots-menu');
        threeDotsMenu.addEventListener('click', (event) => {

            event.stopPropagation();
            let deleteBtn = document.createElement('button');
            let renameBtn = document.createElement('button');
            renameBtn.innerText = 'Rename Folder';
            renameBtn.classList.add('btn', 'btn-primary', 'rename-folder-btn');
            renameBtn.addEventListener('click', async (event) => {
                event.stopPropagation();
                let newName = prompt("Enter the new folder name:", item.name);
                console.log(newName);
                data = {
                    "folder_id": item.id,
                    "new_name": newName
                }
                // Send POST request to server to rename the folder
                console.log("Renaming folder with ID:", item.id);
                const options = {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    'Content-Type': 'application/json',
                    'body': JSON.stringify(data)
                }
                let response = await fetch('/rename-folder', options);
                result = await response.json();
                console.log(result);
                if (result.error) {
                    alert(result.error);
                    return;
                }
                dataFolderTree = result;
                // Re-render the items list
                currentFolder = selectCurrentFolder();
                renderItems(currentFolder);
            });
            deleteBtn.classList.add('btn', 'btn-danger', 'delete-folder-btn');
            deleteBtn.innerText = 'Delete Folder';
            deleteBtn.addEventListener('click', async (event) => {
                event.stopPropagation();
                const userConfirmation = confirm("Are you sure you want to delete this folder and all its contents?");
                if (userConfirmation) {
                    data = {
                        "folder_id": item.id,
                    }
                    // Send DELETE request to server to delete the folder
                    console.log("Deleting folder with ID:", item.id);
                    const options = {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        'Content-Type': 'application/json',
                        'body': JSON.stringify(data)
                    }
                    let response = await fetch('/delete-folder', options);
                    result = await response.json();
                    console.log(result);
                    if (result.error) {
                        alert(result.error);
                        return;
                    }
                    dataFolderTree = result;
                    // Re-render the items list
                    currentFolder = selectCurrentFolder();
                    renderItems(currentFolder);
                }
            });

            let threeDotMenu = document.createElement('div');
            threeDotMenu.appendChild(deleteBtn);
            threeDotMenu.appendChild(renameBtn);
            threeDotMenu.classList.add('three-dots-menu-content');
            // Toggle delete button visibility
            if (!listItem.querySelector('.delete-folder-btn')) {
                closeOtherThreeDotsMenu(event)
                listItem.appendChild(threeDotMenu);
            } else {
                let existingBtn = listItem.querySelector('.three-dots-menu-content');
                listItem.removeChild(existingBtn);
            }
        });
        threeDotsMenu.innerHTML = '⋮';
        listItem.appendChild(threeDotsMenu);
        itemsList.appendChild(listItem);
    k++;

    }
    let i = 0;
    for (let item of currentFolder.links) {
        let listItem = document.createElement('li');
        listItem.innerHTML = `<span>🔗 ${item.name} </span><a href="${item.url}" class="btn btn-primary" target="_blank" id="${i}-link-btn">Go to link</a>`;
        listItem.addEventListener('click', () => {
            // toggle the visibility of the description modal
            description = item.description ? item.description : "No description provided.";
            if  (!listItem.querySelector('.description-modal')) {
                closeOtherLinksDesc(event);
                let modal = document.createElement('div');
                modal.classList.add('description-modal');
                modal.innerHTML = `
                    <div class="description-content">
                        <p id="description-container"></p>
                        <button class="btn btn-danger" id="delete-link-btn">Delete link</button>
                        <button class="btn btn-secondary" id="rename-link-btn">Rename link</button>
                    </div>
                `;
                let descriptionContainer = modal.querySelector('#description-container');
                // description is set this way for security reasons (to prevent XSS)
                descriptionContainer.textContent = description;
                listItem.appendChild(modal);  
                let renameLinkBtn = modal.querySelector('#rename-link-btn');
                renameLinkBtn.addEventListener('click', async () => {
                    const newName = prompt("Enter the new link name:", item.name);
                    console.log(newName);
                    data = {
                        "link_id": item.id,
                        "new_name": newName
                    }
                    // Send POST request to server to rename the link
                    console.log("Renaming link with ID:", item.id);
                    const options = {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        'Content-Type': 'application/json',
                        'body': JSON.stringify(data)
                    }
                    let response = await fetch('/rename-link', options);
                    result = await response.json();
                    console.log(result);
                    if (result.error) {
                        alert(result.error);
                        return;
                    }
                    dataFolderTree = result;
                    // Re-render the items list
                    currentFolder = selectCurrentFolder();
                    renderItems(currentFolder);
                });
                let deleteLinkBtn = modal.querySelector('#delete-link-btn');
                deleteLinkBtn.addEventListener('click', async () => {
                    const userConfirmation = confirm("Are you sure you want to delete this link?");
                    if (userConfirmation) {
                        data = {
                            "link_id": item.id,
                        }
                        // Send DELETE request to server to delete the link
                        console.log("Deleting link with ID:", item.id);
                        const options = {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            'Content-Type': 'application/json',
                            'body': JSON.stringify(data)
                        }
                        let response = await fetch('/delete-link', options);
                        result = await response.json();
                        console.log(result);
                        if (result.error) {
                            alert(result.error);
                            return;
                        }
                        dataFolderTree = result;
                        // Re-render the items lis
                        currentFolder = selectCurrentFolder();

                        renderItems(currentFolder);
                    }

                });  
            } else {
                let modal = listItem.querySelector('.description-modal');
                listItem.removeChild(modal);
            }

        });
        itemsList.appendChild(listItem);
        i++;
    }
}

// Function that closes link description modals when clicking outside
const closeOtherLinksDesc = (event) => {
    let modals = document.querySelectorAll('.description-modal');
    modals.forEach(modal => {
        if (event.target !== modal && !modal.contains(event.target)) {
            modal.parentElement.removeChild(modal);
        }
    });
};
const closeOtherThreeDotsMenu = (event) => {
    let modals = document.querySelectorAll('.three-dots-menu-content');
    modals.forEach(modal => {
        if (event.target !== modal && !modal.contains(event.target)) {
            modal.parentElement.removeChild(modal);
        }
    });
}

// Initial render
renderItems(currentFolder);
newLinkBtn.addEventListener('click', () => {
    newFolderBtn.style.display = 'none';
    newLinkBtn.style.display = 'none';
    let form = document.createElement('form');
    form.method = 'POST';
    form.classList.add("formal-form");
    form.action = '/create_link';
    form.innerHTML = `
        <input autocomplete="off" class="form-control" type="text" name="link_name" placeholder="Link Name" required>
        <input autocomplete="off" class="form-control" type="url" name="link_url" placeholder="Link URL" required>
        <textarea autocomplete="off" rows="7" class="form-control formal-form-textarea" name="link_description" placeholder="Link Description (optional)"></textarea>
        <button class="btn btn-primary" id="submit-link-btn" type="submit">Create Link</button>
        <button class="btn btn-danger" type="button" id="cancel-link-btn">Cancel</button>
    `;
    folders.appendChild(form);
    let cancelLinkBtn = document.getElementById('cancel-link-btn');
    cancelLinkBtn.addEventListener('click', () => {
        folders.removeChild(form);
        newFolderBtn.style.display = 'inline-block';
        newLinkBtn.style.display = 'inline-block';
    });
    let submitLinkBtn = document.getElementById('submit-link-btn');
    let linkNameInput = form.querySelector('input[name="link_name"]');
    let linkUrlInput = form.querySelector('input[name="link_url"]');
    let linkDescrInput = form.querySelector('textarea[name="link_description"]');
    submitLinkBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        data = {
            "name": linkNameInput.value,
            "url": linkUrlInput.value,
            "description": linkDescrInput.value,
            "current_folder": currentFolderId
        }
        console.log(data);
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            'Content-Type': 'application/json',
            'body': JSON.stringify(data)
        }
        let response = await fetch('/create-link', options);
        result = await response.json();
        if (result.error) {
            alert(result.error);
            return;
        }
        dataFolderTree = result;
        // Remove the form
        folders.removeChild(form);
        currentFolder = selectCurrentFolder();
        renderItems(currentFolder);
        newFolderBtn.style.display = 'inline-block';
        newLinkBtn.style.display = 'inline-block';
    });
});
newFolderBtn.addEventListener('click', () => {
    newFolderBtn.style.display = 'none';
    newLinkBtn.style.display = 'none';
    let form = document.createElement('form');
    form.method = 'POST';
    form.classList.add("formal-form");
    form.action = '/create_folder';
    form.innerHTML = `
        <input autocomplete="off" class="form-control" type="text" name="folder_name" placeholder="Folder Name" required>
        <button class="btn btn-primary" id="submit-folder-btn" type="submit">Create Link</button>
        <button class="btn btn-danger" type="button" id="cancel-folder-btn">Cancel</button>
    `;
    folders.appendChild(form);
    let cancelFolderBtn = document.getElementById('cancel-folder-btn');
    cancelFolderBtn.addEventListener('click', () => {
        folders.removeChild(form);
        newFolderBtn.style.display = 'inline-block';
        newLinkBtn.style.display = 'inline-block';
    });
    let submitFolderBtn = document.getElementById('submit-folder-btn');
    let folderNameInput = form.querySelector('input[name="folder_name"]');
    submitFolderBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        data = {
            "name": folderNameInput.value,
            "current_folder": currentFolderId
        }
        console.log(data);
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            'Content-Type': 'application/json',
            'body': JSON.stringify(data)
        }
        let response = await fetch('/create-folder', options);
        result = await response.json();
        if (result.error) {
            alert(result.error);
            return;
        }
        dataFolderTree = result;
        // Remove the form
        folders.removeChild(form);
        currentFolder = selectCurrentFolder();
        renderItems(currentFolder);
        newFolderBtn.style.display = 'inline-block';
        newLinkBtn.style.display = 'inline-block';
    });
});

