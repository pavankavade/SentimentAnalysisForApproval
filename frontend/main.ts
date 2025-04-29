import { sendApprovalRequest } from './api';

// Get DOM elements
const approvalForm = document.getElementById('approval-form') as HTMLFormElement;
const serviceLineInput = document.getElementById('service-line') as HTMLInputElement;
const thresholdInput = document.getElementById('threshold') as HTMLInputElement;
const approvalSection = document.getElementById('approval-section') as HTMLDivElement;
const justificationTextarea = document.getElementById('justification') as HTMLTextAreaElement;
const replyTextarea = document.getElementById('reply') as HTMLTextAreaElement;
const sendReplyButton = document.getElementById('send-reply') as HTMLButtonElement;
const resultMessageDiv = document.getElementById('result-message') as HTMLDivElement;

let currentServiceLine = '';
let currentThreshold = 0;

// Handle initial form submission
approvalForm.addEventListener('submit', (event) => {
    event.preventDefault(); // Prevent default form submission

    currentServiceLine = serviceLineInput.value;
    currentThreshold = parseInt(thresholdInput.value, 10);
    resultMessageDiv.textContent = ''; // Clear previous result
    approvalSection.style.display = 'none'; // Hide approval section initially

    if (currentThreshold > 30) {
        // Prepare justification email content
        justificationTextarea.value = `Subject: Approval Request for ${currentServiceLine}

Please review and approve the task associated with Service Line: ${currentServiceLine} which has a threshold of ${currentThreshold}.

Thanks.`;
        approvalSection.style.display = 'block'; // Show the approval section
    } else {
        // Automatically approved
        resultMessageDiv.textContent = 'Task automatically approved (Threshold <= 30).';
        // Optionally, you could send this to the backend for logging
        // sendApprovalRequest(currentServiceLine, currentThreshold, '', 'Auto-approved');
    }
});

// Handle reply submission
sendReplyButton.addEventListener('click', async () => {
    const userReply = replyTextarea.value;
    const justificationEmail = justificationTextarea.value; // Already populated

    if (!userReply.trim()) {
        alert('Please enter your reply.');
        return;
    }

    resultMessageDiv.textContent = 'Processing...'; // Show feedback
    sendReplyButton.disabled = true; // Disable button during processing

    try {
        const result = await sendApprovalRequest(currentServiceLine, currentThreshold, justificationEmail, userReply);
        // Display result from backend
        resultMessageDiv.textContent = `Backend Response: ${result.status}`; // Adjust based on actual backend response structure
        approvalSection.style.display = 'none'; // Hide section after processing
        approvalForm.reset(); // Reset the initial form
        replyTextarea.value = ''; // Clear reply textarea

    } catch (error) {
        console.error('Error sending reply:', error);
        resultMessageDiv.textContent = `Error: ${(error as Error).message}`; // Display error
    } finally {
        sendReplyButton.disabled = false; // Re-enable button
    }
}); 