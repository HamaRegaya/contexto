document.addEventListener('DOMContentLoaded', () => {
    const guessInput = document.getElementById('guessInput');
    const submitButton = document.getElementById('submitGuess');
    const giveUpButton = document.getElementById('giveUpButton');
    const guessesList = document.getElementById('guessesList');
    const notification = document.getElementById('notification');
    const dailyNumberElement = document.getElementById('dailyNumber');
    const totalPlayersElement = document.getElementById('totalPlayers');
    const tutorial = document.getElementById('tutorial');
    const closeTutorialButton = document.getElementById('closeTutorial');

    let guesses = [];
    
    // Show tutorial if it's the user's first visit
    if (!localStorage.getItem('tutorialSeen')) {
        tutorial.style.display = 'block';
    } else {
        tutorial.style.display = 'none';
    }

    closeTutorialButton.addEventListener('click', () => {
        tutorial.style.display = 'none';
        localStorage.setItem('tutorialSeen', 'true');
    });

    // Load game stats
    async function loadStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            dailyNumberElement.textContent = data.dailyNumber;
            totalPlayersElement.textContent = data.totalPlayers.toLocaleString();
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    function showNotification(message, isError = false) {
        notification.textContent = message;
        notification.style.backgroundColor = isError ? '#ffebee' : '#e8f5e9';
        notification.style.color = isError ? '#c62828' : '#2e7d32';
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }

    function getColorClass(similarity) {
        const percentage = similarity * 100;
        if (percentage >= 50) return 'high-similarity';
        if (percentage >= 35) return 'medium-similarity';
        return 'low-similarity';
    }

    function addGuessToList(word, similarity, isCorrect = false) {
        const guessItem = document.createElement('div');
        guessItem.className = 'guess-item';
        
        // Convert similarity to positive percentage
        const percentage = Math.abs(similarity * 100).toFixed(1);
        const colorClass = getColorClass(Math.abs(similarity));
        guessItem.classList.add(colorClass);
        guessItem.classList.add('slide-in');
        
        const wordSpan = document.createElement('span');
        wordSpan.textContent = word;
        wordSpan.className = 'guess-word';
        
        const similaritySpan = document.createElement('span');
        similaritySpan.className = 'similarity-score';
        similaritySpan.textContent = percentage + '%';
        
        if (isCorrect) {
            guessItem.classList.add('correct-guess');
            guessItem.classList.add('pulse-animation');
        }
        
        guessItem.appendChild(wordSpan);
        guessItem.appendChild(similaritySpan);
        
        guessesList.insertBefore(guessItem, guessesList.firstChild);
        
        // Remove slide-in class after animation
        setTimeout(() => {
            guessItem.classList.remove('slide-in');
        }, 500);
    }

    async function makeGuess(word) {
        try {
            const response = await fetch('/api/guess', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ word }),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                addGuessToList(word, data.similarity, data.isCorrect);
                
                if (data.isCorrect) {
                    showNotification('🎉 Congratulations! You found the word! 🎉');
                    guessInput.disabled = true;
                    submitButton.disabled = true;
                    document.querySelector('.game-container').classList.add('victory-animation');
                }
                
                return true;
            } else {
                showNotification(data.error, true);
                return false;
            }
        } catch (error) {
            showNotification('An error occurred. Please try again.', true);
            return false;
        }
    }

    async function handleGiveUp() {
        try {
            const response = await fetch('/api/give-up', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Add the correct word to the list with 100% similarity
                addGuessToList(data.word, 1.0, true);
                
                // Show the give up message
                showNotification(`Game Over! ${data.message}`, false);
                
                // Disable input and buttons
                guessInput.disabled = true;
                submitButton.disabled = true;
                giveUpButton.disabled = true;
                
                // Add a sad animation to the game container
                document.querySelector('.game-container').classList.add('game-over-animation');
            }
        } catch (error) {
            showNotification('An error occurred. Please try again.', true);
        }
    }

    function handleSubmit() {
        const word = guessInput.value.trim().toLowerCase();
        
        if (!word) {
            showNotification('Please enter a word', true);
            return;
        }
        
        if (guesses.includes(word)) {
            showNotification('You already tried this word', true);
            return;
        }
        
        makeGuess(word).then(success => {
            if (success) {
                guesses.push(word);
                guessInput.value = '';
                guessInput.focus();
            }
        });
    }

    submitButton.addEventListener('click', handleSubmit);
    
    guessInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSubmit();
        }
    });

    giveUpButton.addEventListener('click', () => {
        if (confirm('Are you sure you want to give up? The word will be revealed!')) {
            handleGiveUp();
        }
    });
    
    // Initial load
    loadStats();
    
    // Refresh stats periodically
    setInterval(loadStats, 60000);
});
