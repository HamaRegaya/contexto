document.addEventListener('DOMContentLoaded', () => {
    const guessInput = document.getElementById('guessInput');
    const submitButton = document.getElementById('submitGuess');
    const giveUpButton = document.getElementById('giveUpButton');
    const restartButton = document.getElementById('restartButton');
    const guessesList = document.getElementById('guessesList');
    const notification = document.getElementById('notification');
    const turnIndicator = document.getElementById('turnIndicator');
    const tutorial = document.getElementById('tutorial');
    const closeTutorialButton = document.getElementById('closeTutorial');
    const leaderboardList = document.getElementById('leaderboard-list');

    let isHumanTurn = true;
    let gameOver = false;
    let allGuesses = [];
    let lastAIGuessWord = null;  // Track the last AI guess word

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

    function playSound(soundId) {
        const sound = document.getElementById(soundId);
        if (sound) {
            sound.currentTime = 0;
            sound.play().catch(e => console.log('Sound play failed:', e));
        }
    }

    function showNotification(message, isError = false, duration = 3000) {
        notification.textContent = message;
        notification.className = isError ? 'notification error' : 'notification success';
        notification.style.display = 'block';
        
        // Only set timeout if duration is greater than 0
        if (duration > 0) {
            setTimeout(() => {
                notification.style.display = 'none';
            }, duration);
        }
    }

    function getRankClass(rank) {
        if (rank === 1) return 'rank-0';  // Correct answer gets rank-0 (green)
        
        // For ranks 2-1000, scale from 10-100
        // Lower ranks should get lower numbers (greener colors)
        const maxRank = 1000;
        const normalizedRank = Math.min(rank, maxRank);
        const scaledValue = ((normalizedRank - 1) / (maxRank - 1)) * 90;
        const colorClass = Math.min(Math.floor(scaledValue / 10) * 10 + 10, 100);
        
        return `rank-${colorClass}`;
    }

    function formatRank(rank) {
        if (rank === 1) {
            playSound('correctSound');
            return 'CORRECT!';
        }
        // Play sound based on rank
        if (rank <= 1000) {
            playSound('closeSound');
        } else {
            playSound('farSound');
        }
        return `${rank.toLocaleString()}`;
    }

    function addGuessToList(word, rank, isAI = false, isCorrect = false) {
        // Update last AI guess if this is an AI guess
        if (isAI) {
            lastAIGuessWord = word;
        }
        
        // Add to our guesses array
        allGuesses.push({ word, rank, isAI, isCorrect });
        
        // Sort guesses by rank (best to worst)
        allGuesses.sort((a, b) => a.rank - b.rank);
        
        // Clear the list
        guessesList.innerHTML = '';
        
        // Rebuild the entire list
        allGuesses.forEach(guess => {
            const listItem = document.createElement('div');
            listItem.className = `guess-item ${getRankClass(guess.rank)}`;
            if (guess.isCorrect) listItem.classList.add('correct');
            if (isAI && guess.word === lastAIGuessWord) listItem.classList.add('ai-last-guess');
            
            const wordSpan = document.createElement('span');
            wordSpan.className = 'word';
            wordSpan.textContent = guess.word;
            
            const playerSpan = document.createElement('span');
            playerSpan.className = `player ${guess.isAI ? 'ai-player' : 'human-player'}`;
            playerSpan.innerHTML = guess.isAI ? 
                '<i class="fas fa-robot"></i> AI' : 
                '<i class="fas fa-user"></i> You';
            
            const rankSpan = document.createElement('span');
            rankSpan.className = 'rank';
            rankSpan.textContent = formatRank(guess.rank);
            
            listItem.appendChild(wordSpan);
            listItem.appendChild(playerSpan);
            listItem.appendChild(rankSpan);
            
            guessesList.appendChild(listItem);
        });
    }

    async function startNewGame() {
        try {
            const response = await fetch('/api/start', {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                isHumanTurn = true;
                gameOver = false;
                allGuesses = []; // Reset guesses array
                lastAIGuessWord = null; // Reset last AI guess
                guessesList.innerHTML = '';
                guessInput.disabled = false;
                submitButton.disabled = false;
                guessInput.value = '';
                updateTurnIndicator();
                showNotification('New game started with a new target word!');
            }
        } catch (error) {
            console.error('Error starting new game:', error);
            showNotification('Failed to start new game', true);
        }
    }

    function updateTurnIndicator() {
        if (gameOver) {
            turnIndicator.innerHTML = `
                <div class="turn-content">
                    <i class="fas fa-trophy"></i>
                    <span class="turn-text">Game Over!</span>
                </div>`;
            turnIndicator.className = 'turn-indicator game-over';
            playSound('correctSound');
        } else {
            const humanIcon = '<i class="fas fa-user human-icon"></i>';
            const aiIcon = '<i class="fas fa-robot ai-icon"></i>';
            const thinkingDots = '<div class="ai-thinking"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>';
            
            turnIndicator.innerHTML = `
                <div class="turn-content">
                    ${humanIcon}
                    <span class="turn-text">${isHumanTurn ? 'Your Turn!' : 'AI is thinking...'}</span>
                    ${aiIcon}
                </div>
                ${!isHumanTurn ? thinkingDots : ''}`;
            
            turnIndicator.className = `turn-indicator ${isHumanTurn ? 'human-turn' : 'ai-turn'}`;
            
            // Play turn sound
            playSound(isHumanTurn ? 'humanTurnSound' : 'aiTurnSound');
        }
        
        // Update eyes container
        const eyesContainer = document.querySelector('.eyes-container');
        if (eyesContainer) {
            eyesContainer.className = `eyes-container ${isHumanTurn ? 'human-turn' : 'ai-turn'}`;
        }
    }

    async function makeGuess(word) {
        if (!word || gameOver || !isHumanTurn) return;
        
        try {
            const response = await fetch('/api/guess', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ guess: word })
            });
            
            const data = await response.json();
            
            if (data.status === 'error') {
                showNotification(data.message, true);
                return;
            }
            
            // Add human guess
            addGuessToList(word, data.rank, false, data.game_over && data.winner === 'human');
            
            // If AI's turn, add delay and show thinking animation
            if (!data.game_over) {
                isHumanTurn = false;
                updateTurnIndicator();
                
                // Wait for 3 seconds before showing AI's guess
                await new Promise(resolve => setTimeout(resolve, 3000));
                
                if (data.ai_guess) {
                    addGuessToList(data.ai_guess, data.ai_rank, true, data.game_over && data.winner === 'ai');
                }
            }
            
            // Update game state
            gameOver = data.game_over;
            isHumanTurn = !data.game_over;
            
            // Show game over message if needed
            if (data.game_over) {
                const winner = data.winner === 'human' ? 'You won!' : 'AI won!';
                showNotification(winner);
                guessInput.disabled = true;
                submitButton.disabled = true;
            }
            
            updateTurnIndicator();
            guessInput.value = '';
            
        } catch (error) {
            console.error('Error making guess:', error);
            showNotification('Failed to submit guess', true);
        }
    }

    async function handleGiveUp() {
        if (gameOver) return;
        
        try {
            const response = await fetch('/api/give-up', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                gameOver = true;
                showNotification(`Game Over! The word was: ${data.target_word}`);
                guessInput.disabled = true;
                submitButton.disabled = true;
                updateTurnIndicator();
            }
        } catch (error) {
            console.error('Error giving up:', error);
            showNotification('Failed to give up', true);
        }
    }

    async function handleAIGuess() {
        try {
            const response = await fetch('/api/ai_guess');
            const data = await response.json();

            if (data.status === 'success') {
                const { word, rank } = data;
                lastAIGuessWord = word;
                addGuessToList(word, rank, true);
                
                if (rank === 1) {
                    // AI won
                    gameOver = true;
                    guessInput.disabled = true;
                    submitButton.disabled = true;
                    showNotification(`AI wins! The word was "${word}"`, false, 0);  // Keep notification visible
                    playSound('correctSound');
                } else {
                    isHumanTurn = true;
                    updateTurnIndicator();
                    playSound('humanTurnSound');
                }
            }
        } catch (error) {
            console.error('Error during AI guess:', error);
            showNotification('Error during AI turn', true);
        }
    }

    function handleSubmit() {
        const word = guessInput.value.trim().toLowerCase();
        if (word) {
            makeGuess(word);
        }
    }

    submitButton.addEventListener('click', handleSubmit);
    giveUpButton.addEventListener('click', handleGiveUp);
    restartButton.addEventListener('click', startNewGame);
    
    guessInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSubmit();
        }
    });
    

    // Start a new game when the page loads
    startNewGame();
});
