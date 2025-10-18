class StreetSafetyNavigator {
    constructor() {
        this.character = document.getElementById('character');
        this.characterText = this.character.nextElementSibling;
        this.safetyPanel = document.getElementById('safetyPanel');
        
        this.currentX = 185;
        this.currentY = 162;
        this.currentStreet = null;
        this.visitedStreets = new Set();
        this.moveStep = 15;

        // Street data with randomized safety (hidden initially)
        this.streets = {
            "Main Street": {
                safety: this.getRandomSafety(),
                description: "Primary commercial street through downtown",
                bounds: { minX: 0, maxX: 800, minY: 150, maxY: 175 }
            },
            "Central Avenue": {
                safety: this.getRandomSafety(),
                description: "Mixed residential and commercial area",
                bounds: { minX: 0, maxX: 800, minY: 290, maxY: 315 }
            },
            "Oak Boulevard": {
                safety: this.getRandomSafety(),
                description: "Residential street with tree-lined sidewalks",
                bounds: { minX: 0, maxX: 800, minY: 420, maxY: 445 }
            },
            "First Street": {
                safety: this.getRandomSafety(),
                description: "Historic district with vintage shops",
                bounds: { minX: 175, maxX: 195, minY: 0, maxY: 600 }
            },
            "Second Street": {
                safety: this.getRandomSafety(),
                description: "Business district with office buildings",
                bounds: { minX: 305, maxX: 325, minY: 0, maxY: 600 }
            },
            "Third Street": {
                safety: this.getRandomSafety(),
                description: "Quiet residential area",
                bounds: { minX: 495, maxX: 515, minY: 0, maxY: 600 }
            },
            "Fourth Street": {
                safety: this.getRandomSafety(),
                description: "Entertainment district with restaurants",
                bounds: { minX: 635, maxX: 655, minY: 0, maxY: 600 }
            },
            "North Road": {
                safety: this.getRandomSafety(),
                description: "Northern perimeter road",
                bounds: { minX: 0, maxX: 800, minY: 25, maxY: 45 }
            },
            "South Street": {
                safety: this.getRandomSafety(),
                description: "Southern industrial area",
                bounds: { minX: 0, maxX: 800, minY: 575, maxY: 600 }
            }
        };

        this.setupEventListeners();
        this.checkCurrentStreet();
    }

    getRandomSafety() {
        const safetyLevels = ['safe', 'caution', 'unsafe'];
        return safetyLevels[Math.floor(Math.random() * safetyLevels.length)];
    }

    setupEventListeners() {
        document.addEventListener('keydown', (e) => {
            e.preventDefault();
            switch(e.key) {
                case 'ArrowUp': this.moveCharacter('up'); break;
                case 'ArrowDown': this.moveCharacter('down'); break;
                case 'ArrowLeft': this.moveCharacter('left'); break;
                case 'ArrowRight': this.moveCharacter('right'); break;
            }
        });
    }

    moveCharacter(direction) {
        let newX = this.currentX;
        let newY = this.currentY;

        switch(direction) {
            case 'up':
                newY -= this.moveStep;
                break;
            case 'down':
                newY += this.moveStep;
                break;
            case 'left':
                newX -= this.moveStep;
                break;
            case 'right':
                newX += this.moveStep;
                break;
        }

        // Check if new position is on a valid street
        const streetAtPosition = this.getStreetAtPosition(newX, newY);
        
        if (streetAtPosition && this.isValidPosition(newX, newY)) {
            this.currentX = newX;
            this.currentY = newY;
            this.updateCharacterPosition();
            
            // Check if we entered a new street
            if (this.currentStreet !== streetAtPosition) {
                this.currentStreet = streetAtPosition;
                this.revealStreetSafety(streetAtPosition);
            }
        }
    }

    isValidPosition(x, y) {
        // Keep character within map bounds
        return x >= 10 && x <= 790 && y >= 10 && y <= 590;
    }

    getStreetAtPosition(x, y) {
        for (const [streetName, data] of Object.entries(this.streets)) {
            const bounds = data.bounds;
            if (x >= bounds.minX && x <= bounds.maxX && 
                y >= bounds.minY && y <= bounds.maxY) {
                return streetName;
            }
        }
        return null;
    }

    updateCharacterPosition() {
        this.character.setAttribute('cx', this.currentX);
        this.character.setAttribute('cy', this.currentY);
        this.characterText.setAttribute('x', this.currentX);
        this.characterText.setAttribute('y', this.currentY + 5);
    }

    revealStreetSafety(streetName) {
        const streetData = this.streets[streetName];
        if (!streetData) return;

        // Mark street as visited and color it
        if (!this.visitedStreets.has(streetName)) {
            this.visitedStreets.add(streetName);
            this.colorVisitedStreet(streetName, streetData.safety);
        }

        this.updateSafetyPanel(streetName, streetData);
    }

    colorVisitedStreet(streetName, safety) {
        const streetElements = document.querySelectorAll(`[data-street="${streetName}"]`);
        streetElements.forEach(element => {
            element.classList.add('visited', safety);
        });
    }

    updateSafetyPanel(streetName, streetData) {
        const { safety, description } = streetData;
        
        const safetyInfo = {
            safe: {
                icon: '✅',
                status: 'Safe Zone',
                message: 'Street is safe',
                tips: 'This area has good lighting, regular foot traffic, and security presence. Safe for walking at all times.'
            },
            caution: {
                icon: '⚠️',
                status: 'Caution Zone',
                message: 'Be careful',
                tips: 'Exercise caution in this area. Stay alert, avoid walking alone late at night, and consider alternate routes if possible.'
            },
            unsafe: {
                icon: '🚨',
                status: 'Unsafe Zone',
                message: 'Danger detected',
                tips: 'HIGH RISK AREA: Poor lighting, isolated location, or recent incidents reported. Avoid if possible, especially after dark.'
            }
        };

        const info = safetyInfo[safety];
        
        this.safetyPanel.className = `safety-panel ${safety}`;
        this.safetyPanel.innerHTML = `
            <div class="safety-status">
                <span class="safety-icon">${info.icon}</span>
                <span>${info.status} – ${info.message}</span>
            </div>
            <div class="street-name">${streetName}</div>
            <div class="safety-description">${description}</div>
            <div class="safety-tips ${safety}">
                <strong>Safety Tips:</strong><br>
                ${info.tips}
            </div>
        `;
    }

    checkCurrentStreet() {
        const streetAtPosition = this.getStreetAtPosition(this.currentX, this.currentY);
        if (streetAtPosition) {
            this.currentStreet = streetAtPosition;
            this.revealStreetSafety(streetAtPosition);
        }
    }

    resetCharacter() {
        // Reset to starting position
        this.currentX = 185;
        this.currentY = 162;
        this.currentStreet = null;
        
        // Clear visited streets
        this.visitedStreets.clear();
        
        // Reset street colors
        const visitedStreets = document.querySelectorAll('.street.visited');
        visitedStreets.forEach(street => {
            street.classList.remove('visited', 'safe', 'caution', 'unsafe');
        });
        
        // Re-randomize safety levels
        Object.keys(this.streets).forEach(streetName => {
            this.streets[streetName].safety = this.getRandomSafety();
        });
        
        // Reset panel
        this.safetyPanel.className = 'safety-panel';
        this.safetyPanel.innerHTML = `
            <div class="initial-message">
                <h3>🚶‍♀️ Start Exploring</h3>
                <p>Use arrow keys to navigate through the streets. Safety information will be revealed as you explore different areas.</p>
            </div>
        `;
        
        this.updateCharacterPosition();
        this.checkCurrentStreet();
    }
}

// Initialize the navigator
const navigator = new StreetSafetyNavigator();

// Global functions for button controls
function moveCharacter(direction) {
    navigator.moveCharacter(direction);
}

function resetCharacter() {
    navigator.resetCharacter();
}
