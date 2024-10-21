// Initialize speech recognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.lang = 'en-US';
recognition.interimResults = false;
recognition.continuous = true;

let listeningForCommand = false;
let commandInProgress = false; // Prevents duplicate commands

// Recipient mapping (Merchant IDs instead of UPI IDs)
const recipientMapping = {
    "rishi": "P9GTBIcYKh6YH36", // Replace with Akshat's actual Razorpay Merchant ID
    "john": "merchant_id_789012", // Add more mappings as needed
};

// Start listening for "Hello UPI" trigger word
recognition.onresult = function (event) {
    const transcript = event.results[event.results.length - 1][0].transcript.trim().toLowerCase();
    console.log(`Transcript: ${transcript}`); // Debugging log
    
    if (transcript === "hello upi" && !listeningForCommand) {
        listeningForCommand = true;
        appendMessage('bot', "Voice command activated! You can now speak your command.");
        recognition.stop(); // Stop listening for "Hello UPI"
        startCommandRecognition(); // Start listening for a single command
    }
};

// Ensure recognition restarts if it unexpectedly stops
recognition.onend = function() {
    if (!listeningForCommand) {
        recognition.start(); // Keep listening for "Hello UPI" if recognition is stopped unexpectedly
    }
};

// Start listening for "Hello UPI"
recognition.start();

function startCommandRecognition() {
    const commandRecognition = new SpeechRecognition();
    commandRecognition.lang = 'en-US';
    commandRecognition.interimResults = false;

    // Handle the user's command once recognized
    commandRecognition.onresult = function (event) {
        if (commandInProgress) return; // Prevent duplicate handling
        commandInProgress = true; // Mark command processing in progress
        const voiceCommand = event.results[0][0].transcript.toLowerCase().trim();

        // Extract amount and recipient from command
        const match = voiceCommand.match(/send (\d+) rupees to (\w+)/);
        if (match) {
            const amount = match[1];
            const recipientName = match[2].toLowerCase();
            
            // Check if recipient is mapped
            if (recipientMapping[recipientName]) {
                const recipientMerchantID = recipientMapping[recipientName];
                appendMessage('bot', `Voice command received: Sending ${amount} rupees to ${recipientName}...`);

                // Prompt for PIN before payment
                promptForPin(amount, recipientMerchantID, recipientName);
            } else {
                appendMessage('bot', `Sorry, I don't recognize the recipient: ${recipientName}.`);
            }
        } else {
            appendMessage('user', voiceCommand); // Show other recognized commands in the chat
        }

        commandInProgress = false; // Reset the flag after processing
        
        // Stop listening for commands and reset state
        commandRecognition.stop(); // Stop listening after handling one command
        listeningForCommand = false; // Reset command listening
        appendMessage('bot', "Command processed. Say 'Hello UPI' to activate voice command again.");
        
        // Restart recognition to listen for "Hello UPI" again
        recognition.start(); // Restart listening for "Hello UPI"
    };

    commandRecognition.onend = function() {
        // Restart listening for "Hello UPI" if command recognition ends
        if (!listeningForCommand) {
            recognition.start(); 
        }
    };

    commandRecognition.start(); // Start listening for a single command
}

function promptForPin(amount, recipientMerchantID, recipientName) {
    appendMessage('bot', "Please enter your PIN to proceed.");
    
    // Create an input field for the PIN
    const pinInput = document.createElement('input');
    pinInput.setAttribute('type', 'password');
    pinInput.setAttribute('placeholder', 'Enter PIN');
    pinInput.setAttribute('id', 'pinInput');
    document.getElementById('messages').appendChild(pinInput);

    // Create a button to confirm the PIN
    const confirmPinButton = document.createElement('button');
    confirmPinButton.innerText = 'Confirm PIN';
    confirmPinButton.onclick = function() {
        const enteredPin = document.getElementById('pinInput').value;
        const userId = 'user123'; // Replace with actual user ID

        // Send the payment request with the PIN
        initiatePayment(amount, recipientMerchantID, userId, enteredPin);
    };
    document.getElementById('messages').appendChild(confirmPinButton);
}

function appendMessage(sender, message) {
    let messagesDiv = document.getElementById("messages");
    let messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);
    messageElement.innerHTML = `<div class="bubble">${message}</div>`;
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight; // Scroll to the bottom
}

// Razorpay payment handler (updated for Payouts)
function initiatePayment(amount, recipientMerchantID, userId, pin) {
    appendMessage('bot', "Request sent: Initiating payout...");

    // Call backend to create a payout
    fetch('/create-payout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ amount: amount, merchant_id: recipientMerchantID, user_id: userId, pin: pin }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            appendMessage('bot', `Transaction successful! Payout ID: ${data.payout_id}, Amount: ${data.amount}`);
        } else {
            appendMessage('bot', `Transaction failed: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error creating payout:', error);
        appendMessage('bot', "Transaction failed: Unable to create payout.");
    });
}