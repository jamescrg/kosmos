function updateText() {
    const input = document.getElementById('userInput').value;
    checkSubmitButton(input);
}

function checkSubmitButton(input) {
    const submitButton = document.querySelector('button[form="void-invoice-form"]');
    if (!submitButton) return;
    if (input === 'VOID') {
        submitButton.removeAttribute('disabled');
        submitButton.classList.remove('disabled-btn');
    } else {
        submitButton.setAttribute('disabled', 'disabled');
        submitButton.classList.add('disabled-btn');
    }
}
