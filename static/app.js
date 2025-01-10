document.addEventListener('DOMContentLoaded', () => {
    const guessInput = document.getElementById('guessInput');
    const submitButton = document.getElementById('submitGuess');
    const giveUpButton = document.getElementById('giveUpButton');
    const guessesList = document.getElementById('guessesList');
    const notification = document.getElementById('notification');
    const turnIndicator = document.getElementById('turnIndicator');
    const tutorial = document.getElementById('tutorial');
    const closeTutorialButton = document.getElementById('closeTutorial');
    const leaderboardList = document.getElementById('leaderboard-list');

    let isHumanTurn = true;
    let gameOver = false;
    let allGuesses = [];

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

    function showNotification(message, isError = false) {
        notification.textContent = message;
        notification.style.backgroundColor = isError ? '#ffebee' : '#e8f5e9';
        notification.style.color = isError ? '#c62828' : '#2e7d32';
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }

    function getRankClass(rank) {
        // Convert rank (1-100000) to percentile (0-100)
        const percentile = Math.floor((rank / 100000) * 100);
        // Map percentile to one of our 11 color classes (0-100 in steps of 10)
        const colorClass = Math.min(Math.floor(percentile / 10) * 10, 100);
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
        return `#${rank.toLocaleString()}`;
    }

    function addGuessToList(word, rank, isAI = false, isCorrect = false) {
        // Add to our guesses array
        allGuesses.push({ word, rank, isAI, isCorrect });
        
        // Sort guesses by rank (worst to best)
        allGuesses.sort((a, b) => b.rank - a.rank);
        
        // Clear the list
        guessesList.innerHTML = '';
        
        // Rebuild the entire list
        allGuesses.forEach(guess => {
            const listItem = document.createElement('div');
            listItem.className = `guess-item ${getRankClass(guess.rank)}`;
            if (guess.isCorrect) listItem.classList.add('correct');
            
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
                guessesList.innerHTML = '';
                updateTurnIndicator();
                showNotification('New game started!');
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

    function handleSubmit() {
        const word = guessInput.value.trim().toLowerCase();
        if (word) {
            makeGuess(word);
        }
    }

    submitButton.addEventListener('click', handleSubmit);
    giveUpButton.addEventListener('click', handleGiveUp);
    
    guessInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSubmit();
        }
    });
    
    function updateLeaderboard(word, rank, isHuman) {
        const leaderboardList = document.getElementById('leaderboard-list');
        const existingItem = Array.from(leaderboardList.children).find(item => 
            item.querySelector('.word-text').textContent === word
        );

        if (existingItem) {
            return; // Word already in leaderboard
        }

        const li = document.createElement('li');
        li.className = 'leaderboard-item';
        
        // Calculate progress percentage (inverted since lower rank is better)
        // Using 9999 as max rank, 1 as min rank
        const progressPercent = 100 - ((rank - 1) / (9999 - 1)) * 100;
        
        // Determine background and text colors based on rank
        let bgColor, textColor;
        if (rank === 1) {
            bgColor = '#1b5e20'; // Dark green for correct
            textColor = '#ffffff';
        } else if (rank <= 100) {
            bgColor = '#2e7d32'; // Green
            textColor = '#ffffff';
        } else if (rank <= 500) {
            bgColor = '#388e3c'; // Light green
            textColor = '#ffffff';
        } else if (rank <= 1000) {
            bgColor = '#ffa000'; // Amber
            textColor = '#ffffff';
        } else if (rank <= 3000) {
            bgColor = '#f57c00'; // Dark orange
            textColor = '#ffffff';
        } else if (rank <= 5000) {
            bgColor = '#e64a19'; // Deep orange
            textColor = '#ffffff';
        } else if (rank <= 7000) {
            bgColor = '#d32f2f'; // Red
            textColor = '#ffffff';
        } else {
            bgColor = '#b71c1c'; // Dark red
            textColor = '#ffffff';
        }

        li.style.backgroundColor = bgColor;
        li.style.color = textColor;

        li.innerHTML = `
            <div class="word-info">
                <span class="word-text">${word}</span>
                <span class="player-indicator ${isHuman ? 'human' : 'ai'}">
                    <i class="fas ${isHuman ? 'fa-user' : 'fa-robot'}"></i>
                </span>
                <span class="rank" style="color: ${textColor}">#${rank}</span>
            </div>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: ${progressPercent}%; background-color: rgba(255, 255, 255, 0.3)"></div>
            </div>
        `;

        // Find the correct position to insert the new item (sorted by rank)
        const items = Array.from(leaderboardList.children);
        const insertIndex = items.findIndex(item => {
            const itemRank = parseInt(item.querySelector('.rank').textContent.slice(1));
            return rank < itemRank;
        });

        if (insertIndex === -1) {
            leaderboardList.appendChild(li); // Add to end if no better position found
        } else {
            leaderboardList.insertBefore(li, items[insertIndex]);
        }

        // Play appropriate sound based on rank
        if (rank === 1) {
            playSound('correct');
        } else if (rank <= 500) {
            playSound('close');
        } else {
            playSound('far');
        }
    }

    // Start a new game when the page loads
    startNewGame();
});
