# HalloweenUltraCatch
# 🎃 Halloween Ultra Catch - 12 Powerups

This project is a **hand-tracking augmented reality game** built with Python, OpenCV, MediaPipe, and Pygame. Players use real‑hand gestures captured via webcam to control a paddle, catch falling pumpkins (balls), avoid ghosts, and collect magical power‑ups in a Halloween‑themed arena.

---

## ✨ Features

- 🖐️ **Hand Tracking Control** – Real‑time hand detection using MediaPipe; move your index finger to steer the paddle.
- 🎃 **Dynamic Falling Objects** – Pumpkin balls spawn with increasing difficulty.
- ⚡ **12 Unique Power‑ups** – Each power‑up changes gameplay (grow/shrink paddle, slow motion, magnet, ghost attacks, bombs, time rewind, shield, double points, multi‑ball, freeze, witch blessing/curse).
- 👻 **Angry Ghost Enemies** – Flying ghosts that deflect balls and shrink your paddle on contact.
- 💥 **Particle System** – Explosions, sparks, and magical effects for every collision and power‑up.
- 🧠 **Active Effect Management** – Real‑time UI timers for temporary buffs/debuffs.
- 🛡️ **Memory & Game State Safety** – Sensitive game variables are cleared/reset between rounds.
- 🏆 **Score & Lives System** – Keep track of high‑score chases; shield prevents life loss.

---

## 🔒 Security Design (Cryptographic Analogy)

Although this is a **game** (not a cryptographic tool), the architecture follows similar safety principles as secure systems:

1. **Input Validation** – Hand landmark coordinates are clamped and smoothed to avoid out‑of‑bounds crashes.
2. **State Isolation** – Each game loop resets temporary flags (`shield_active`, `double_points`, etc.) to prevent lingering effects.
3. **Resource Cleanup** – `cv2.VideoCapture` and `pygame` resources are released after game over.
4. **Separation of Concerns** – Rendering, logic, collision, and effect management are kept in distinct code blocks.

> ⚠️ *This is an entertainment application. No actual encryption or password hashing is performed – the "RSA‑AES" style heading is used only as a template format. For real cryptographic needs, see the first project example.*

---

## 📁 Project Structure
halloween_ultra_catch/
├── main.py # Main game source code (hand tracking + game loop)
└── README.md # Project documentation (this file)


text

---

## 🧠 Theoretical & Mathematical Foundations

- **Hand Tracking** – MediaPipe’s machine learning model maps 21 hand landmarks in real time.
- **Collision Detection** – Axis‑aligned bounding box (AABB) for paddle vs. ball + Euclidean distance for ghosts.
- **Particle Physics** – Simple Euler integration with gravity (`vy += 0.08`) for realistic sparks.
- **Smoothing Algorithm** – Exponential moving average (`smoothed = smoothed*(1-α) + new*α`) to reduce hand jitter.
- **Power‑up Spawn Logic** – Pseudo‑random selection with decreasing intervals (dynamic difficulty).

For detailed mathematical derivations, see [Cryptography & Game Math Notes](#) *(placeholder link)*.

---

## 🎮 How It Works

1. **Player places hand in front of webcam** – Index finger tip controls the paddle’s X position.
2. **Orange pumpkin balls fall from the top** – Catch them with the coffin‑shaped paddle.
3. **Power‑ups fall occasionally** – Catch them with the paddle to activate special effects.
4. **Ghosts float and deflect balls** – They also shrink your paddle if they hit you.
5. **Lives decrease when a ball is missed** – Unless a shield power‑up is active.
6. **Game ends when lives reach zero** – Raise your hand to restart, press ESC to exit.

---

## 📋 Prerequisites

| Requirement      | Details                               |
|----------------|---------------------------------------|
| **Platform**    | Windows / macOS / Linux               |
| **Python**      | 3.8 or higher                         |
| **Webcam**      | Any standard USB or built‑in camera   |
| **Dependencies**| Install via `pip install -r requirements.txt` |

### Required Libraries
- `opencv-python`
- `mediapipe`
- `pygame`
- `numpy`

---

## 🚀 Installation & Run

1. **Clone the repository**
   ```bash
   git clone https://github.com/AsmaJamshidian/HalloweenUltraCatch-Game.git
   cd HalloweenUltraCatch-Game
Install dependencies

bash
pip install -r requirements.txt
Run the game

bash
python main.py
Allow webcam access when prompted.

🕹️ Controls
Action	Method
Move paddle left / right	Move your index finger horizontally
Restart after game over	Raise any hand in front of camera
Exit game	Press ESC key
🔧 Configuration (Customization)
Open main.py and edit the CONFIG section:

python
WIN_W, WIN_H = 1000, 700      # Window size
PADDLE_W, PADDLE_H = 650, 36  # Base paddle dimensions
BALL_RADIUS = 18              # Pumpkin size
BALL_SPEED_MIN, BALL_SPEED_MAX = 3, 6
FPS = 60
SMOOTHING = 0.25              # Hand movement smoothing factor
📜 License
This project is licensed under the MIT License – see the LICENSE file for details.

👩‍💻 Authors
Asma – Game mechanics & particle effects

Mooud – Hand tracking integration & power‑up system

🙌 Acknowledgments
MediaPipe team for real‑time hand landmark detection.

Pygame community for game development framework.

Halloween spirit for the spooky inspiration.

🎃 Have fun catching pumpkins – and don’t let the ghosts get you! 🧙‍♀️
