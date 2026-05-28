const width = 8;
const candyColors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange'];
const board = document.getElementById('board');
const scoreDisplay = document.getElementById('score');
let squares = [];
let score = 0;
let levelCleared = false; 

// Target Management Object
let levelTargets = {
    red: 0,
    blue: 0,
    green: 0
};

// Dragging Variables
let colorBeingDragged;
let colorBeingReplaced;
let squareIdBeingDragged;
let squareIdBeingReplaced;

// 1. Random Targets Generate Karne Ka Function
function generateNewTargets() {
    levelTargets.red = Math.floor(Math.random() * 11) + 15;   // 15 se 25 ke beech random target
    levelTargets.blue = Math.floor(Math.random() * 11) + 15;
    levelTargets.green = Math.floor(Math.random() * 11) + 15;
    updateTargetUI();
}

// Target UI Display Update karna
function updateTargetUI() {
    document.getElementById('target-red').innerText = levelTargets.red > 0 ? levelTargets.red : "✅";
    document.getElementById('target-blue').innerText = levelTargets.blue > 0 ? levelTargets.blue : "✅";
    document.getElementById('target-green').innerText = levelTargets.green > 0 ? levelTargets.green : "✅";
}

// 2. Board Create Karna
function createBoard() {
    board.innerHTML = ''; 
    squares = [];
    generateNewTargets(); // Naya target generate karein
    levelCleared = false;

    for (let i = 0; i < width * width; i++) {
        const candy = document.createElement('div');
        candy.setAttribute('class', 'candy');
        candy.setAttribute('draggable', true);
        candy.setAttribute('id', i);
        
        let randomColor = candyColors[Math.floor(Math.random() * candyColors.length)];
        candy.classList.add(randomColor);
        
        candy.addEventListener('dragstart', dragStart);
        candy.addEventListener('dragover', (e) => e.preventDefault());
        candy.addEventListener('drop', dragDrop);
        candy.addEventListener('dragend', dragEnd);

        board.appendChild(candy);
        squares.push(candy);
    }
}

// Drag & Drop Handlers
function dragStart() {
    if (this.classList.contains('color-bomb')) {
        colorBeingDragged = 'color-bomb';
    } else {
        colorBeingDragged = candyColors.find(color => this.classList.contains(color));
    }
    squareIdBeingDragged = parseInt(this.id);
}

function dragDrop() {
    if (this.classList.contains('color-bomb')) {
        colorBeingReplaced = 'color-bomb';
    } else {
        colorBeingReplaced = candyColors.find(color => this.classList.contains(color));
    }
    squareIdBeingReplaced = parseInt(this.id);
}

// Galat match hone par shoor (sound) machane wala function
function playErrorSound() {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();

    oscillator.type = 'sawtooth'; // Shoor machane ke liye buzzy sound
    oscillator.frequency.setValueAtTime(120, audioCtx.currentTime); // Low pitch warning
    
    gainNode.gain.setValueAtTime(0.2, audioCtx.currentTime); // Volume control
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3); // Fade out

    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);

    oscillator.start();
    oscillator.stop(audioCtx.currentTime + 0.3);
}

// Centralized DragEnd Function (Power bomb + Error Handling ke sath)
function dragEnd() {
    let validMoves = [
        squareIdBeingDragged - 1,
        squareIdBeingDragged + 1,
        squareIdBeingDragged - width,
        squareIdBeingDragged + width
    ];
    let validMove = validMoves.includes(squareIdBeingReplaced);

    if (squareIdBeingReplaced && validMove) {
        
        // --- POWER BOMB LOGIC ---
        if (colorBeingDragged === 'color-bomb' && colorBeingReplaced && colorBeingReplaced !== 'color-bomb') {
            blastAllOfColor(colorBeingReplaced);
            squares[squareIdBeingDragged].className = 'candy ' + candyColors[Math.floor(Math.random() * candyColors.length)];
            return;
        }
        if (colorBeingReplaced === 'color-bomb' && colorBeingDragged && colorBeingDragged !== 'color-bomb') {
            blastAllOfColor(colorBeingDragged);
            squares[squareIdBeingReplaced].className = 'candy ' + candyColors[Math.floor(Math.random() * candyColors.length)];
            return;
        }

        // Normal Candies Swap
        let classDragged = squares[squareIdBeingDragged].className;
        let classReplaced = squares[squareIdBeingReplaced].className;

        squares[squareIdBeingDragged].className = classReplaced;
        squares[squareIdBeingReplaced].className = classDragged;
        
        let matchFound = checkAllMatches();

        // --- AGAR GALAT MATCH HUA (NO MATCH FOUND) ---
        if (!matchFound) {
            playErrorSound(); // Shoor machao!

            // Dono candies ko shake karo
            squares[squareIdBeingDragged].classList.add('shake-error');
            squares[squareIdBeingReplaced].classList.add('shake-error');

            // 300ms baad wapas apni jagah
            setTimeout(() => {
                squares[squareIdBeingDragged].className = classDragged;
                squares[squareIdBeingReplaced].className = classReplaced;
                squares[squareIdBeingDragged].classList.remove('shake-error');
                squares[squareIdBeingReplaced].classList.remove('shake-error');
            }, 300);
        }
    } else if (squareIdBeingReplaced && !validMove) {
        // Galat direction me drag karne par bhi shoor machao
        playErrorSound();
    }
}

// Color Bomb Blast Engine: Pure board se us color ko saaf karna aur target minus karna
function blastAllOfColor(color) {
    let count = 0;
    squares.forEach(square => {
        if (square.classList.contains(color)) {
            square.className = 'candy'; 
            count++;
            
            if (levelTargets[color] !== undefined && levelTargets[color] > 0) {
                levelTargets[color]--;
            }
        }
    });
    score += count * 15;
    scoreDisplay.innerHTML = score;
    updateTargetUI();
    checkTargetAchieved();
}

// Target check engine
function checkTargetAchieved() {
    if (levelTargets.red <= 0 && levelTargets.blue <= 0 && levelTargets.green <= 0 && !levelCleared) {
        levelCleared = true; 
        sendLevelCompleteToBackend();
    }
}

// Central Matches Matcher (5 -> 4 -> 3 precedence)
function checkAllMatches() {
    let m5Row = checkRowForFive();
    let m5Col = checkColumnForFive();
    let m4Row = checkRowForFour();
    let m4Col = checkColumnForFour();
    let m3Row = checkRowForThree();
    let m3Col = checkColumnForThree();

    return (m5Row || m5Col || m4Row || m4Col || m3Row || m3Col);
}

// Candies count update logic
function trackDestroyedCandy(color) {
    if (levelTargets[color] !== undefined && levelTargets[color] > 0) {
        levelTargets[color]--;
        updateTargetUI();
    }
}

// MATCH-5 (Color Bomb Maker)
function checkRowForFive() {
    for (let i = 0; i < 60; i++) {
        let rowOfFive = [i, i+1, i+2, i+3, i+4];
        if (i % width > 3) continue;
        let decidedColor = candyColors.find(c => squares[i].classList.contains(c));
        if (!decidedColor) continue;

        if (rowOfFive.every(index => squares[index].classList.contains(decidedColor))) {
            score += 50;
            scoreDisplay.innerHTML = score;
            rowOfFive.forEach((index, pos) => {
                trackDestroyedCandy(decidedColor);
                if (pos === 2) {
                    squares[index].className = 'candy color-bomb'; 
                } else {
                    squares[index].className = 'candy';
                }
            });
            checkTargetAchieved();
            return true;
        }
    }
    return false;
}

function checkColumnForFive() {
    for (let i = 0; i < 32; i++) {
        let colOfFive = [i, i+width, i+(width*2), i+(width*3), i+(width*4)];
        let decidedColor = candyColors.find(c => squares[i].classList.contains(c));
        if (!decidedColor) continue;

        if (colOfFive.every(index => squares[index].classList.contains(decidedColor))) {
            score += 50;
            scoreDisplay.innerHTML = score;
            colOfFive.forEach((index, pos) => {
                trackDestroyedCandy(decidedColor);
                if (pos === 2) {
                    squares[index].className = 'candy color-bomb';
                } else {
                    squares[index].className = 'candy';
                }
            });
            checkTargetAchieved();
            return true;
        }
    }
    return false;
}

// MATCH-4 (Normal Blast)
function checkRowForFour() {
    for (let i = 0; i < 61; i++) {
        let rowOfFour = [i, i+1, i+2, i+3];
        if (i % width > 4) continue;
        let decidedColor = candyColors.find(c => squares[i].classList.contains(c));
        if (!decidedColor) continue;

        if (rowOfFour.every(index => squares[index].classList.contains(decidedColor))) {
            score += 30;
            scoreDisplay.innerHTML = score;
            rowOfFour.forEach(index => {
                trackDestroyedCandy(decidedColor);
                squares[index].className = 'candy';
            });
            checkTargetAchieved();
            return true;
        }
    }
    return false;
}

function checkColumnForFour() {
    for (let i = 0; i < 40; i++) {
        let colOfFour = [i, i+width, i+(width*2), i+(width*3)];
        let decidedColor = candyColors.find(c => squares[i].classList.contains(c));
        if (!decidedColor) continue;

        if (colOfFour.every(index => squares[index].classList.contains(decidedColor))) {
            score += 30;
            scoreDisplay.innerHTML = score;
            colOfFour.forEach(index => {
                trackDestroyedCandy(decidedColor);
                squares[index].className = 'candy';
            });
            checkTargetAchieved();
            return true;
        }
    }
    return false;
}

// MATCH-3 (Normal Blast)
function checkRowForThree() {
    let matchFound = false;
    for (let i = 0; i < 62; i++) {
        let rowOfThree = [i, i+1, i+2];
        if (i % width > 5) continue;
        let decidedColor = candyColors.find(c => squares[i].classList.contains(c));
        if (!decidedColor) continue;

        if (rowOfThree.every(index => squares[index].classList.contains(decidedColor))) {
            score += 15;
            scoreDisplay.innerHTML = score;
            rowOfThree.forEach(index => {
                trackDestroyedCandy(decidedColor);
                squares[index].className = 'candy'; 
            });
            matchFound = true;
            checkTargetAchieved();
        }
    }
    return matchFound;
}

function checkColumnForThree() {
    let matchFound = false;
    for (let i = 0; i < 48; i++) {
        let columnOfThree = [i, i+width, i+(width*2)];
        let decidedColor = candyColors.find(c => squares[i].classList.contains(c));
        if (!decidedColor) continue;

        if (columnOfThree.every(index => squares[index].classList.contains(decidedColor))) {
            score += 15;
            scoreDisplay.innerHTML = score;
            columnOfThree.forEach(index => {
                trackDestroyedCandy(decidedColor);
                squares[index].className = 'candy'; 
            });
            matchFound = true;
            checkTargetAchieved();
        }
    }
    return matchFound;
}

// 3. Gravity System (Infinite auto drops)
function moveIntoSquareBelow() {
    for (let i = 0; i < 55; i++) {
        if (squares[i + width].className === 'candy' || squares[i + width].className === '') {
            squares[i + width].className = squares[i].className;
            squares[i].className = 'candy';
        }
        
        const firstRow = [0, 1, 2, 3, 4, 5, 6, 7];
        if (firstRow.includes(i) && (squares[i].className === 'candy' || squares[i].className === '')) {
            let randomColor = candyColors[Math.floor(Math.random() * candyColors.length)];
            squares[i].className = 'candy ' + randomColor;
        }
    }
}

// Backend API Level Sync
function sendLevelCompleteToBackend() {
    const csrftoken = getCookie('csrftoken');
    fetch('/api/complete-level/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert("🎉 Target Achieved! Level Completed! " + data.message);
            document.getElementById('coins').innerText = data.new_coins;
            document.getElementById('level').innerText = data.new_level;
            score = 0;
            scoreDisplay.innerHTML = score;
            createBoard(); 
        }
    })
    .catch(error => console.error('Error:', error));
}

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

// Custom Song Player Logic
document.getElementById('bg-music-upload').addEventListener('change', function(e) {
    const file = e.target.files[0];
    const audio = document.getElementById('bg-audio');
    if (file) {
        audio.src = URL.createObjectURL(file);
        audio.play().catch(error => console.log("Audio play failed:", error));
    }
});

// Initialize Board on Load
createBoard();

// Continuous Loop for Gravity and Real-time Matches
window.setInterval(function() {
    moveIntoSquareBelow();
    checkAllMatches();
}, 200);