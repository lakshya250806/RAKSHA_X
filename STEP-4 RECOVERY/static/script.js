// ...existing code...
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const loading = document.getElementById('loading');

        // Auto-resize and focus
        messageInput.focus();
        
        // Send message on Enter key
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        sendButton.addEventListener('click', sendMessage);

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            // Add user message to chat
            addMessage(message, 'user');
            messageInput.value = '';
            
            // Disable input while processing
            setLoading(true);

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }

                // Add bot response to chat
                addMessage(data.response, 'bot');
                
            } catch (error) {
                console.error('Error:', error);
                addMessage('I apologize, but I\'m having trouble connecting right now. Please try again in a moment, or reach out to a mental health professional if you need immediate support.', 'bot');
            } finally {
                setLoading(false);
            }
        }

        function addMessage(content, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const avatar = document.createElement('div');
            avatar.className = 'avatar';
            avatar.textContent = sender === 'user' ? 'You' : '🧠';
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            messageContent.textContent = content;
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(messageContent);
            
            // Remove welcome message if it exists
            const welcomeMessage = document.querySelector('.welcome-message');
            if (welcomeMessage) {
                welcomeMessage.remove();
            }
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function setLoading(isLoading) {
            loading.style.display = isLoading ? 'block' : 'none';
            sendButton.disabled = isLoading;
            messageInput.disabled = isLoading;
            
            if (!isLoading) {
                messageInput.focus();
            }
        }

        async function showCrisisResources() {
            const resources = `
🆘 CRISIS RESOURCES 🆘

IMMEDIATE HELP:
• US: National Suicide Prevention Lifeline - 988
• US: Crisis Text Line - Text HOME to 741741
• Emergency Services: 911 (US), 999 (UK), 112 (EU)

If you're having thoughts of self-harm or suicide, please reach out immediately:
• Call emergency services
• Contact a trusted friend or family member  
• Go to your nearest emergency room
• Call a crisis helpline

Remember: You are not alone, and help is available. 💙

Would you like to talk about what you're going through?
            `.trim();
            
            addMessage(resources, 'bot');
        }

        // Check for crisis keywords in messages
        function containsCrisisKeywords(message) {
            const crisisKeywords = ['suicide', 'kill myself', 'end it all', 'don\'t want to live', 'harm myself'];
            return crisisKeywords.some(keyword => message.toLowerCase().includes(keyword));
        }

        // Override addMessage to check for crisis situations
        const originalAddMessage = addMessage;
        addMessage = function(content, sender) {
            originalAddMessage(content, sender);
            
            if (sender === 'user' && containsCrisisKeywords(content)) {
                setTimeout(() => {
                    showCrisisResources();
                }, 1000);
            }
        };
// ...existing code...