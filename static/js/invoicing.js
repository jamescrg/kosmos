function updateText() {
    const input = document.getElementById('userInput').value;
    checkSubmitButton(input);
}

function checkSubmitButton(input) {
    const submitButton = document.querySelector('.submit');
    if (input === 'VOID') {
        submitButton.removeAttribute('disabled');
        submitButton.classList.remove('disabled-btn');
    } else {
        submitButton.setAttribute('disabled', 'disabled');
        submitButton.classList.add('disabled-btn');
    }
}
