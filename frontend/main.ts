import { sendApprovalRequest } from './api';

// Get DOM elements
const approvalForm = document.getElementById('approval-form') as HTMLFormElement;
const serviceLineInput = document.getElementById('service-line') as HTMLInputElement;
const thresholdInput = document.getElementById('threshold') as HTMLInputElement;
const approvalSection = document.getElementById('approval-section') as HTMLDivElement;
const approvalEmailTextarea = document.getElementById('approval-email') as HTMLTextAreaElement;
const replyTextarea = document.getElementById('reply') as HTMLTextAreaElement;
const sendReplyButton = document.getElementById('send-reply') as HTMLButtonElement;
const resultMessageDiv = document.getElementById('result-message') as HTMLDivElement;

const clarificationSection = document.getElementById('clarification-section') as HTMLDivElement;
const clarificationMessage = document.getElementById('clarification-message') as HTMLTextAreaElement;
const hiringManagerReplyTextarea = document.getElementById('hiring-manager-reply') as HTMLTextAreaElement;
const sendClarificationButton = document.getElementById('send-clarification') as HTMLButtonElement;

let currentServiceLine = '';
let currentThreshold = 0;
let lastApprovalPayload: any = null;

// Handle initial form submission
approvalForm.addEventListener('submit', (event) => {
    event.preventDefault(); // Prevent default form submission

    currentServiceLine = serviceLineInput.value;
    currentThreshold = parseInt(thresholdInput.value, 10);
    resultMessageDiv.textContent = ''; // Clear previous result
    approvalSection.style.display = 'none'; // Hide approval section initially

    if (currentThreshold > 30) {
        // Prepare approval email content
        approvalEmailTextarea.value = `Subject: Action Required: ${currentServiceLine}

Please review the request for Service Line: ${currentServiceLine} (Threshold: ${currentThreshold}).

Your confirmation is needed to proceed. Please reply with your decision.

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
    const approvalEmail = approvalEmailTextarea.value; // Already populated

    if (!userReply.trim()) {
        alert('Please enter your reply.');
        return;
    }

    resultMessageDiv.textContent = 'Processing...'; // Show feedback
    sendReplyButton.disabled = true; // Disable button during processing

    try {
        const result = await sendApprovalRequest(currentServiceLine, currentThreshold, approvalEmail, userReply);
        if (result.status === 'Clarification') {
            // Show clarification section
            clarificationSection.style.display = 'block';
            approvalSection.style.display = 'none';
            lastApprovalPayload = {
                serviceLine: currentServiceLine,
                threshold: currentThreshold,
                approvalEmail,
                userReply
            };
            resultMessageDiv.textContent = 'Clarification required. Please provide details as hiring manager.';
            return;
        }
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

// Clarification submit handler
if (sendClarificationButton) {
    sendClarificationButton.addEventListener('click', async () => {
        const hiringManagerReply = hiringManagerReplyTextarea.value;
        if (!hiringManagerReply.trim()) {
            alert('Please enter the hiring manager reply.');
            return;
        }
        resultMessageDiv.textContent = 'Processing clarification...';
        sendClarificationButton.disabled = true;
        try {
            const payload = {
                ...lastApprovalPayload,
                hiringManagerReply
            };
            const response = await fetch('http://localhost:8000/process-clarification', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    service_line: payload.serviceLine,
                    threshold: payload.threshold,
                    approval_email: payload.approvalEmail,
                    user_reply: payload.userReply,
                    hiring_manager_reply: hiringManagerReply
                })
            });
            if (!response.ok) {
                let errorDetail = `HTTP error! status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorDetail += ` - ${errorData.detail || JSON.stringify(errorData)}`;
                } catch (e) {}
                throw new Error(errorDetail);
            }
            const result = await response.json();
            if (result.status === 'Approved' && result.extracted_data) {
                resultMessageDiv.textContent = `Approved. Extracted Data: ${JSON.stringify(result.extracted_data)}`;
            } else {
                resultMessageDiv.textContent = `Backend Response: ${result.status}`;
            }
            clarificationSection.style.display = 'none';
            approvalForm.reset();
            hiringManagerReplyTextarea.value = '';
        } catch (error) {
            console.error('Error sending clarification:', error);
            // Try to extract missing fields from error message
            const errMsg = (error as Error).message || '';
            const missingMatch = errMsg.match(/Missing fields: (.+)$/);
            if (missingMatch) {
                resultMessageDiv.textContent = `Error: Missing required fields: ${missingMatch[1]}`;
            } else {
                resultMessageDiv.textContent = `Error: ${errMsg}`;
            }
        } finally {
            sendClarificationButton.disabled = false;
        }
    });
}