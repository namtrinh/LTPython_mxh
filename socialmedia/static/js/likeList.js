const showLikeListBtn = document.getElementById('showLikeListBtn');
const likeListModal = new bootstrap.Modal(document.getElementById('likeListModal'));
const likeListContent = document.getElementById('likeListContent');

// Giả sử liked_users là danh sách người đã like (có thể lấy từ server)
const liked_users = [
    { username: 'user1', profile_img: '/static/user1.jpg' },
    { username: 'user2', profile_img: '/static/user2.jpg' },
    { username: 'user3', profile_img: '/static/user3.jpg' }
];

// Hàm hiển thị danh sách người đã like vào modal
function showLikeList() {
    let contentHtml = '<ul class="list-unstyled">';

    // Duyệt qua liked_users và tạo danh sách
    liked_users.forEach(user => {
        contentHtml += `
            <li class="user-item d-flex align-items-center py-2">
                <a href="/profile/${user.username}" class="username d-flex align-items-center">
                    <img src="${user.profile_img}" alt="Profile Picture" class="user-profile-pic me-3">
                    <span>@${user.username}</span>
                </a>
            </li>
        `;
    });

    contentHtml += '</ul>';

    // Chèn danh sách vào modal
    likeListContent.innerHTML = contentHtml;

    // Mở modal
    likeListModal.show();
}

// Gán sự kiện click cho nút "Xem danh sách người đã like"
showLikeListBtn.addEventListener('click', showLikeList);