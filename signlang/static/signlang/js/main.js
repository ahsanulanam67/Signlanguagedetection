$(document).ready(function() {
    // Configuration
    const UPDATE_INTERVAL = 300; // ms
    const STATUS_COLORS = {
        detected: 'green',
        cooldown: 'orange',
        ready: 'blue',
        error: 'red'
    };

    // DOM Elements
    const $currentSentence = $('#current-sentence');
    const $signFeedback = $('#sign-feedback');
    const $speakBtn = $('#speak-btn');
    const $clearBtn = $('#clear-btn');

   
    // Set up CSRF token for AJAX requests
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Update sentence display
    function updateSentence() {
        $.ajax({
            url: "{% url 'get_sentence' %}",
            type: "GET",
            headers: { "X-CSRFToken": csrftoken },
            success: function(data) {
                const displayText = data.sentence || 'Start signing to build your sentence';
                $currentSentence.text(displayText);
            },
            error: function() {
                console.error('Failed to fetch sentence');
            },
            complete: function() {
                setTimeout(updateSentence, UPDATE_INTERVAL);
            }
        });
    }

    // Update sign detection feedback
    function updateFeedback() {
        $.ajax({
            url: "{% url 'sign_status' %}",
            type: "GET",
            headers: { "X-CSRFToken": csrftoken },
            success: function(data) {
                if (data.confirmed_sign) {
                    showFeedback(`Detected: ${data.confirmed_sign}`, STATUS_COLORS.detected);
                } else if (data.in_cooldown) {
                    showFeedback(`Please wait: ${data.cooldown_remaining.toFixed(1)}s`, 
                               STATUS_COLORS.cooldown);
                } else {
                    showFeedback('Ready for next sign', STATUS_COLORS.ready);
                }
            },
            error: function() {
                showFeedback('Error getting sign status', STATUS_COLORS.error);
            },
            complete: function() {
                setTimeout(updateFeedback, UPDATE_INTERVAL);
            }
        });
    }

    // Helper to show feedback with color
    function showFeedback(message, color) {
        $signFeedback.removeClass('alert-success alert-warning alert-info alert-danger')
                   .addClass(`alert-${color}`)
                   .text(message);
    }

    // Speak button handler
    $speakBtn.click(function() {
        $.ajax({
            url: "{% url 'speak_sentence' %}",
            type: "POST",
            headers: { "X-CSRFToken": csrftoken },
            success: function(data) {
                if (data.status === 'spoken') {
                    alert('Speaking: ' + $currentSentence.text());
                } else {
                    alert('No sentence to speak');
                }
            },
            error: function() {
                alert('Failed to speak sentence');
            }
        });
    });

    // Clear button handler
    $clearBtn.click(function() {
        $.ajax({
            url: "{% url 'clear_sentence' %}",
            type: "POST",
            headers: { "X-CSRFToken": csrftoken },
            success: function(data) {
                if (data.status === 'cleared') {
                    $currentSentence.text('Start signing to build your sentence');
                }
            },
            error: function() {
                alert('Failed to clear sentence');
            }
        });
    });

    // Start periodic updates
    updateSentence();
    updateFeedback();
});