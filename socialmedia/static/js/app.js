document.addEventListener("DOMContentLoaded", function() {
    const toggleButtons = document.querySelectorAll('.toggle-comment');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault(); // Ngăn chặn hành động mặc định của liên kết
            const targetId = this.getAttribute('data-target'); // Lấy giá trị của thuộc tính data-target
            const commentSection = document.querySelector(targetId); // Tìm phần bình luận tương ứng

            // Chuyển đổi hiển thị của phần bình luận
            if (commentSection.style.display === "none" || commentSection.style.display === "") {
                commentSection.style.display = "block"; // Hiện phần bình luận
            } else {
                commentSection.style.display = "none"; // Ẩn phần bình luận
            }
        });
    });
});