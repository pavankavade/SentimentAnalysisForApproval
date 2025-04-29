// Placeholder for API communication logic

const API_BASE_URL = 'http://localhost:8000'; // Adjust if your backend runs elsewhere

export async function sendApprovalRequest(serviceLine: string, threshold: number, approvalEmail: string, userReply: string) {
  const payload = {
    service_line: serviceLine,
    threshold: threshold,
    approval_email: approvalEmail,
    user_reply: userReply,
  };

  try {
    const response = await fetch(`${API_BASE_URL}/process-approval`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      // Try to parse error response from backend if possible
      let errorDetail = `HTTP error! status: ${response.status}`;
      try {
          const errorData = await response.json();
          errorDetail += ` - ${errorData.detail || JSON.stringify(errorData)}`;
      } catch (e) {
          // Ignore if response is not JSON or empty
      }
      throw new Error(errorDetail);
    }

    return await response.json(); // Assuming the backend returns JSON
  } catch (error) {
    console.error('API request failed:', error);
    throw error; // Re-throw the error to be handled by the caller
  }
} 