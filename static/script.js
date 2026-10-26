document.addEventListener("DOMContentLoaded", function () {
    const buttons = document.querySelectorAll(".confirm-delete");

    buttons.forEach(function (button) {
        button.addEventListener("click", function (event) {
            if (!confirm("Are you sure you want to delete this skill?")) {
                event.preventDefault();
            }
        });
    });
});
