/**
 * File Upload Form Handler
 *
 * Handles forms with file uploads intelligently:
 * - Uses HTMX for validation when no file is selected
 * - Uses regular form submission when files are present
 */

const initializeFileUploadForms = () => {
  const formsWithFileInputs = document.querySelectorAll(
    'form input[type="file"]',
  );

  formsWithFileInputs.forEach((fileInput) => {
    const form = fileInput.closest("form");

    if (form && !form.dataset.fileUploadInitialized) {
      form.dataset.fileUploadInitialized = "true";

      form.addEventListener("submit", (e) => {
        const hasFile = fileInput.files && fileInput.files.length > 0;

        if (!hasFile) {
          // No file selected, use HTMX for validation
          e.preventDefault();

          const target =
            form.getAttribute("hx-target") ||
            form.getAttribute("data-hx-target") ||
            "#htmx-modal-container";

          // Preserve value from the form
          const formData = new FormData(form);

          fetch(form.action, {
            method: "POST",
            body: formData,
            headers: {
              "X-Requested-With": "XMLHttpRequest",
              "HX-Request": "true",
            },
          })
            .then((response) => response.text())
            .then((html) => {
              document.querySelector(target).innerHTML = html;
              initializeFileUploadForms();
            })
            .catch((error) => console.error("Error:", error));
        } else {
          // File is present, remove HTMX attributes
          form.removeAttribute("hx-post");
          form.removeAttribute("hx-target");
        }
      });
    }
  });
};

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", initializeFileUploadForms);

// Also initialize when HTMX loads new content
document.body.addEventListener("htmx:afterSwap", () => {
  initializeFileUploadForms();
});
