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
    const historyBtn = document.getElementById('historyBtn');
    const historyModal = document.getElementById('historyModal');
    const giveUpModal = document.getElementById('giveUpModal');
    const confirmGiveUpBtn = document.getElementById('confirmGiveUp');
    const cancelGiveUpBtn = document.getElementById('cancelGiveUp');
    const giveUpResult = document.getElementById('giveUpResult');
    const revealedWord = document.getElementById('revealedWord');
    const giveUpStats = document.getElementById('giveUpStats');
    const wordSelector = document.getElementById('wordSelector');

    // Auth Elements
    const loginBtn = document.getElementById('loginBtn');
    const registerBtn = document.getElementById('registerBtn');
    const loginModal = document.getElementById('loginModal');
    const registerModal = document.getElementById('registerModal');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const userInfo = document.getElementById('userInfo');
    const usernameDisplay = document.getElementById('username');
    const logoutBtn = document.getElementById('logoutBtn');
    const closeButtons = document.querySelectorAll('.close-modal');

    let isHumanTurn = true;
    let gameOver = false;
    let allGuesses = [];
    let lastAIGuessWord = null;  // Track the last AI guess word
    let lastHumanGuessWord = null;  // Track the last human guess word
    let thinkingTimer = null;
    let thinkingTime = 0;
    let hintShown = false;

    // Auth State
    let currentUser = null;

    // Check if user is already logged in
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        updateAuthUI(true);
    }

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
        // Update last guess based on player
        if (isAI) {
            lastAIGuessWord = word;
        } else {
            lastHumanGuessWord = word;
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
            if (guess.isCorrect) {
                listItem.classList.add('correct');
                if (guess.isAI) {
                    listItem.classList.add('target-word');
                }
            }
            if (isAI && guess.word === lastAIGuessWord) listItem.classList.add('ai-last-guess');
            if (!isAI && guess.word === lastHumanGuessWord) listItem.classList.add('human-last-guess');
            
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
            // Reset game state
            gameOver = false;
            document.getElementById('guessesList').innerHTML = '';
            document.getElementById('guessInput').value = '';
            document.getElementById('guessInput').disabled = false;
            document.getElementById('submitGuess').disabled = false;
            document.getElementById('submitGuess').style.display = 'block';
            giveUpButton.style.display = 'block';
            
            // Reset give up modal
            giveUpModal.style.display = 'none';
            giveUpResult.style.display = 'none';
            confirmGiveUpBtn.disabled = false;
            cancelGiveUpBtn.style.display = 'block';
            
            // Clear leaderboard
            const leaderboardList = document.getElementById('leaderboard-list');
            if (leaderboardList) {
                leaderboardList.innerHTML = '';
            }
            
            // Reset word selector
            if (wordSelector) {
                wordSelector.value = '';
            }
            
            showNotification('New game started!', false);
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
                body: JSON.stringify({
                    guess: word,
                    user_id: currentUser ? currentUser.user_id : null
                })
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
                if (data.winner === 'ai') {
                    // AI wins animation and message
                    showNotification(`AI Wins! The word was "${data.target_word}"`, false, 0);
                    const gameContainer = document.querySelector('.game-container');
                    gameContainer.classList.add('ai-wins');
                    playSound('correctSound');
                    
                    // Add shake animation to eyes
                    const eyes = document.querySelectorAll('.eye');
                    eyes.forEach(eye => eye.classList.add('ai-win-eye'));
                    
                    setTimeout(() => {
                        gameContainer.classList.remove('ai-wins');
                        eyes.forEach(eye => eye.classList.remove('ai-win-eye'));
                    }, 3000);

                    // Add the target word to the list with green highlight
                    addGuessToList(data.target_word, 1, true, true);
                } else {
                    // Human wins animation and message
                    showNotification('You Won! Congratulations!', false, 0);
                    const gameContainer = document.querySelector('.game-container');
                    gameContainer.classList.add('human-wins');
                    playSound('correctSound');
                    
                    // Add animation to eyes
                    const eyes = document.querySelectorAll('.eye');
                    eyes.forEach(eye => eye.classList.add('human-win-eye'));
                    
                    setTimeout(() => {
                        gameContainer.classList.remove('human-wins');
                        eyes.forEach(eye => eye.classList.remove('human-win-eye'));
                    }, 3000);
                }
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
        giveUpModal.style.display = 'block';
        giveUpResult.style.display = 'none';
    }

    // Cancel give up
    cancelGiveUpBtn.addEventListener('click', () => {
        giveUpModal.style.display = 'none';
    });

    // Confirm give up
    confirmGiveUpBtn.addEventListener('click', async () => {
        confirmGiveUpBtn.disabled = true;
        cancelGiveUpBtn.style.display = 'none';
        
        try {
            const response = await fetch('/api/give-up', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: currentUser ? currentUser.user_id : null
                })
            });
            
            const data = await response.json();
            
            // Show the result
            giveUpResult.style.display = 'block';
            revealedWord.textContent = data.target_word;
            giveUpStats.textContent = `You made ${data.total_guesses} guesses before giving up.`;
            
            // Update game state
            gameOver = true;
            document.getElementById('guessInput').disabled = true;
            document.getElementById('submitGuess').disabled = true;
            giveUpButton.style.display = 'block';
            
            // Update the guess list with the target word
            const guessList = document.getElementById('guessesList');
            const targetWordItem = document.createElement('div');
            targetWordItem.className = 'guess-item rank-0 target-word';
            targetWordItem.innerHTML = `
                <span class="word">${data.target_word}</span>
                <span class="rank">Target Word</span>
            `;
            guessList.appendChild(targetWordItem);
            
        } catch (error) {
            console.error('Error:', error);
            showNotification('Failed to give up', true);
        }
    });

    function handleAIGuess() {
        if (gameOver || !isHumanTurn) return;
        
        fetch('/ai_guess', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ guesses: allGuesses })
        })
        .then(response => response.json())
        .then(data => {
            console.log('AI guess response:', data);
            // Check if AI won
            if (data.ai_rank === 1 || data.winner === 'ai') {
                console.log('AI won! Adding animations...');
                // AI wins animation and message
                showNotification("AI WINS! The word was: " + data.ai_guess, false, 0);
                const gameContainer = document.querySelector('.game-container');
                console.log('Game container:', gameContainer);
                gameContainer.classList.add('ai-wins');
                playSound('correctSound');
                
                // Add shake animation to eyes
                const eyes = document.querySelectorAll('.eye');
                console.log('Eyes elements:', eyes);
                eyes.forEach(eye => eye.classList.add('ai-win-eye'));
                
                setTimeout(() => {
                    gameContainer.classList.remove('ai-wins');
                    eyes.forEach(eye => eye.classList.remove('ai-win-eye'));
                }, 3000);
                
                gameOver = true;
                submitButton.disabled = true;
                giveUpButton.disabled = true;
            }
            
            if (data.ai_guess && data.ai_rank) {
                addGuessToList(data.ai_guess, data.ai_rank, true, data.ai_rank === 1);
            }
            
            isHumanTurn = true;
            updateTurnIndicator();
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error making AI guess', true);
            isHumanTurn = true;
            updateTurnIndicator();
        });
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
    
    // Tutorial button functionality
    const tutorialButton = document.getElementById('tutorialButton');
    tutorialButton.addEventListener('click', () => {
        tutorial.style.display = 'flex';
    });

    closeTutorialButton.addEventListener('click', () => {
        tutorial.style.display = 'none';
    });

    guessInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSubmit();
        }
    });

    // Thinking messages to encourage the player
    const thinkingMessages = [
        "You're doing great! Keep thinking...",
        "You're getting closer...",
        "Take your time, the answer will come to you!",
        "Sometimes the simplest words are the answer...",
        "Try thinking about related concepts..."
    ];

    // Function to update thinking timer
    function updateThinkingTimer() {
        if (!isHumanTurn || gameOver) return;
        
        thinkingTime++;
        const minutes = Math.floor(thinkingTime / 60);
        const seconds = thinkingTime % 60;
        
        // Show random encouraging message every 20 seconds
        if (thinkingTime % 20 === 0) {
            const randomMessage = thinkingMessages[Math.floor(Math.random() * thinkingMessages.length)];
            showNotification(randomMessage, false, 3000);
        }

        // Show hint after 45 seconds of thinking
        if (thinkingTime === 45 && !hintShown) {
            provideHint();
        }

        // Add thinking animation to input
        guessInput.classList.toggle('thinking');
    }

    // Function to provide a hint based on previous guesses
    function provideHint() {
        if (allGuesses.length === 0) return;
        
        // Find the best guess so far
        const bestGuess = allGuesses.reduce((prev, current) => 
            prev.rank < current.rank ? prev : current
        );

        const hintMessage = `💡 Hint: Your closest guess was "${bestGuess.word}" (rank ${bestGuess.rank}). Try thinking of related words!`;
        showNotification(hintMessage, false, 2000);
        hintShown = true;
    }

    // Start thinking timer when input is focused
    guessInput.addEventListener('focus', () => {
        if (!thinkingTimer && isHumanTurn && !gameOver) {
            thinkingTimer = setInterval(updateThinkingTimer, 1000);
            thinkingTime = 0;
            hintShown = false;
        }
    });

    // Reset thinking timer when guess is submitted
    function resetThinkingTimer() {
        if (thinkingTimer) {
            clearInterval(thinkingTimer);
            thinkingTimer = null;
            thinkingTime = 0;
            hintShown = false;
            guessInput.classList.remove('thinking');
        }
    }

    // Modal Controls
    loginBtn.addEventListener('click', () => {
        loginModal.style.display = 'block';
    });

    registerBtn.addEventListener('click', () => {
        registerModal.style.display = 'block';
    });

    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            loginModal.style.display = 'none';
            registerModal.style.display = 'none';
            historyModal.style.display = 'none';
            giveUpModal.style.display = 'none';
        });
    });

    window.addEventListener('click', (e) => {
        if (e.target === loginModal) loginModal.style.display = 'none';
        if (e.target === registerModal) registerModal.style.display = 'none';
        if (e.target === historyModal) historyModal.style.display = 'none';
        if (e.target === giveUpModal) giveUpModal.style.display = 'none';
    });

    // Form Submissions
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('regUsername').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        const confirmPassword = document.getElementById('regConfirmPassword').value;
        
        if (password !== confirmPassword) {
            showNotification('Passwords do not match', true);
            return;
        }
        
        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, email, password })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showNotification('Registration successful! Please log in.', false);
                registerModal.style.display = 'none';
                loginModal.style.display = 'block';
                registerForm.reset();
            } else {
                showNotification(data.message, true);
            }
        } catch (error) {
            showNotification('An error occurred during registration', true);
            console.error('Registration error:', error);
        }
    });

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (data.success) {
                currentUser = data.user;
                localStorage.setItem('user', JSON.stringify(currentUser));
                showNotification('Login successful!', false);
                loginModal.style.display = 'none';
                updateAuthUI(true);
                loginForm.reset();
            } else {
                showNotification(data.message, true);
            }
        } catch (error) {
            showNotification('An error occurred during login', true);
            console.error('Login error:', error);
        }
    });

    logoutBtn.addEventListener('click', () => {
        currentUser = null;
        localStorage.removeItem('user');
        updateAuthUI(false);
        showNotification('Logged out successfully', false);
    });

    function updateAuthUI(isLoggedIn) {
        if (isLoggedIn && currentUser) {
            loginBtn.style.display = 'none';
            registerBtn.style.display = 'none';
            userInfo.style.display = 'flex';
            usernameDisplay.textContent = currentUser.username;
        } else {
            loginBtn.style.display = 'flex';
            registerBtn.style.display = 'flex';
            userInfo.style.display = 'none';
            usernameDisplay.textContent = 'Guest';
        }
    }

    // Update stats after each game
    async function updateUserStats(score) {
        if (!currentUser) return;
        
        try {
            const response = await fetch('/api/update_stats', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: currentUser.user_id,
                    score: score
                })
            });
            
            const data = await response.json();
            if (!data.success) {
                console.error('Failed to update stats:', data.message);
            }
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }

    // Game History Functions
    async function loadGameHistory() {
        if (!currentUser) return;
        
        try {
            // Load user stats
            const statsResponse = await fetch(`/api/user_stats?user_id=${currentUser.user_id}`);
            const statsData = await statsResponse.json();
            
            if (statsData.success) {
                updateStatsDisplay(statsData.stats);
            }
            
            // Load game history
            const historyResponse = await fetch(`/api/game_history?user_id=${currentUser.user_id}&limit=10`);
            const historyData = await historyResponse.json();
            
            if (historyData.success) {
                updateGameHistoryList(historyData.history);
            }
        } catch (error) {
            console.error('Error loading game history:', error);
            showNotification('Failed to load game history', true);
        }
    }

    function updateStatsDisplay(stats) {
        document.getElementById('totalGames').textContent = stats.total_games;
        document.getElementById('bestRank').textContent = stats.best_rank || '-';
        document.getElementById('completionRate').textContent = `${Math.round(stats.completion_rate)}%`;
        document.getElementById('avgGuesses').textContent = stats.average_guesses;
    }

    function updateGameHistoryList(games) {
        const gameList = document.getElementById('gameHistoryList');
        gameList.innerHTML = '';
        
        games.forEach(game => {
            const gameDate = new Date(game.played_at * 1000);
            const formattedDate = gameDate.toLocaleDateString() + ' ' + gameDate.toLocaleTimeString();
            
            const gameItem = document.createElement('div');
            gameItem.className = `game-item ${game.completed ? 'completed' : 'abandoned'}`;
            
            gameItem.innerHTML = `
                <span class="target-word">${game.target_word}</span>
                <div class="game-stats">
                    <span><i class="fas fa-hashtag"></i> ${game.final_rank}</span>
                    <span><i class="fas fa-clock"></i> ${formatTime(game.time_taken)}</span>
                    <span><i class="fas fa-list-ol"></i> ${game.guesses_count} guesses</span>
                </div>
                <span class="game-date">${formattedDate}</span>
            `;
            
            gameList.appendChild(gameItem);
        });
    }

    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    // History button click handler
    historyBtn.addEventListener('click', () => {
        historyModal.style.display = 'block';
        loadGameHistory();
    });

    // Save game history when game ends
    async function saveGameHistory(targetWord, guessCount, finalRank, timeTaken, completed = true) {
        if (!currentUser) return;
        
        try {
            const response = await fetch('/api/save_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: currentUser.user_id,
                    target_word: targetWord,
                    guesses_count: guessCount,
                    final_rank: finalRank,
                    time_taken: timeTaken,
                    completed: completed
                })
            });
            
            const data = await response.json();
            if (!data.success) {
                console.error('Failed to save game history:', data.message);
            }
        } catch (error) {
            console.error('Error saving game history:', error);
        }
    }

    // Load available words
    async function loadAvailableWords() {
        try {
            const response = await fetch('/api/available-words');
            const data = await response.json();
            
            // Clear existing options
            wordSelector.innerHTML = '';
            
            // Populate the word selector with numbered options
            for (let i = 0; i < data.count; i++) {
                const option = document.createElement('option');
                option.value = i;
                option.textContent = `Word ${i + 1}`;
                wordSelector.appendChild(option);
            }

            // Select Word 1 by default and trigger the change event
            wordSelector.value = '0';
            const changeEvent = new Event('change');
            wordSelector.dispatchEvent(changeEvent);
        } catch (error) {
            console.error('Error loading words:', error);
            showNotification('Failed to load available words', true);
        }
    }

    // Word selection handler
    wordSelector.addEventListener('change', async () => {
        const selectedIndex = parseInt(wordSelector.value);
        if (isNaN(selectedIndex)) return;
        
        // Ask for confirmation if a game is in progress
        if (!gameOver && (document.getElementById('guessesList').children.length > 0)) {
            if (!confirm('Starting a new game will reset your current progress. Continue?')) {
                wordSelector.value = '';
                return;
            }
        }
        
        try {
            const response = await fetch('/api/set-target-word', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ index: selectedIndex })
            });
            
            const data = await response.json();
            if (data.success) {
                // Reset game state
                gameOver = false;
                document.getElementById('guessesList').innerHTML = '';
                document.getElementById('guessInput').value = '';
                document.getElementById('guessInput').disabled = false;
                document.getElementById('submitGuess').disabled = false;
                document.getElementById('submitGuess').style.display = 'block';
                giveUpButton.style.display = 'block';
                
                // Reset give up modal
                giveUpModal.style.display = 'none';
                giveUpResult.style.display = 'none';
                confirmGiveUpBtn.disabled = false;
                cancelGiveUpBtn.style.display = 'block';
                
                // Clear and update leaderboard
                const leaderboardList = document.getElementById('leaderboard-list');
                if (leaderboardList) {
                    leaderboardList.innerHTML = '';
                    if (data.leaderboard && data.leaderboard.leaderboard) {
                        updateLeaderboard(data.leaderboard);
                    }
                }
                
                showNotification(`New game started with Word ${selectedIndex + 1}`, false);
                
                // Reset word selector
                wordSelector.value = '';
            } else {
                showNotification('Failed to start new game', true);
            }
        } catch (error) {
            console.error('Error setting target word:', error);
            showNotification('Failed to start new game', true);
        }
    });

    // Update leaderboard function
    function updateLeaderboard(data) {
        const leaderboardList = document.getElementById('leaderboard-list');
        if (!leaderboardList) return;
        
        leaderboardList.innerHTML = ''; // Clear existing entries
        
        if (data && data.leaderboard) {
            data.leaderboard.forEach(guess => {
                const guessElement = document.createElement('div');
                guessElement.className = `leaderboard-item ${guess.player === 'human' ? 'human-guess' : 'ai-guess'}`;
                guessElement.innerHTML = `
                    <span class="word">${guess.word}</span>
                    <span class="rank">${guess.rank}</span>
                `;
                leaderboardList.appendChild(guessElement);
            });
        }
    }

    // Start a new game when the page loads
    startNewGame();

    // Load available words when the page loads
    loadAvailableWords();
});
