document.addEventListener('DOMContentLoaded', () => {
    const videoCanvas = document.getElementById('videoCanvas');
    const ctx = videoCanvas.getContext('2d');

    const videoWidth = videoCanvas.width;
    const videoHeight = videoCanvas.height;

    let socket = null; // Replace with socket connection if using in a real-time collaborative setting

    let myEquation = '';
    let delayCounter = 0;
    let mode = 'scientific'; // Start with scientific mode initially
    let buttonList = createButtons(mode);

    const mpHands = new Hands({
        locateFile: (file) => {
            return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
        }
    });

    mpHands.onResults(handleHandTracking);

    const camera = new Camera(videoCanvas, {
        onFrame: async () => {
            await mpHands.send({ image: videoCanvas });
        },
        width: videoWidth,
        height: videoHeight
    });

    camera.start();

    function createButtons(mode) {
        let buttonList = [];
        const values = mode === 'scientific' ? scientificButtonValues : standardButtonValues;
        for (let y = 0; y < values.length; y++) {
            for (let x = 0; x < values[y].length; x++) {
                const xpos = x * 80 + 50;
                const ypos = y * 80 + 170;
                buttonList.push(new Button({ x: xpos, y: ypos, width: 80, height: 80, value: values[y][x] }));
            }
        }
        return buttonList;
    }

    function handleHandTracking(results) {
        if (!results.multiHandLandmarks) {
            return;
        }

        const handLandmarks = results.multiHandLandmarks[0];
        let indexX = null, indexY = null, middleX = null, middleY = null;

        for (const [index, landmark] of Object.entries(handLandmarks.landmark)) {
            const x = landmark.x * videoWidth;
            const y = landmark.y * videoHeight;

            if (index === '8') { // Index finger tip
                indexX = x;
                indexY = y;
            } else if (index === '12') { // Middle finger tip
                middleX = x;
                middleY = y;
                break;
            }
        }

        if (indexX !== null && middleX !== null) {
            // Draw circle around index finger tip
            ctx.beginPath();
            ctx.arc(indexX, indexY, 5, 0, 2 * Math.PI);
            ctx.fillStyle = 'red';
            ctx.fill();

            const distance = Math.sqrt((middleX - indexX) ** 2 + (middleY - indexY) ** 2);

            if (distance < 35) {
                for (const button of buttonList) {
                    if (button.checkClick(indexX, indexY) && delayCounter === 0) {
                        let myValue = button.value;

                        if (myValue === '=') {
                            try {
                                myEquation = String(eval(myEquation
                                    .replace('pi', String(Math.PI))
                                    .replace('sqrt', 'Math.sqrt')
                                    .replace('log', 'Math.log10')
                                    .replace('ln', 'Math.log')
                                    .replace('^', '**')
                                    .replace('sin', 'Math.sin')
                                    .replace('cos', 'Math.cos')
                                    .replace('tan', 'Math.tan')));
                            } catch {
                                myEquation = 'Error';
                            }
                        } else if (myValue === 'C') {
                            myEquation = '';
                        } else if (myValue === '<-') {
                            myEquation = myEquation.slice(0, -1);
                        } else {
                            myEquation += myValue;
                        }

                        delayCounter = 1;
                    }
                }
            }

            if (delayCounter !== 0) {
                delayCounter += 1;
                if (delayCounter > 10) {
                    delayCounter = 0;
                }
            }

            ctx.font = '20px Arial';
            ctx.fillStyle = 'white';
            ctx.fillText(myEquation, 60, 100);

            for (const button of buttonList) {
                button.draw(ctx);
            }
        }
    }
});
