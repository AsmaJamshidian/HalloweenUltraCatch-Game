import cv2
import mediapipe as mp
import pygame
import sys
import time
import random
import numpy as np
from collections import deque

# ---------------- CONFIG ----------------
WIN_W, WIN_H = 1000, 700
PADDLE_W, PADDLE_H = 650, 36
BALL_RADIUS = 18
BALL_SPEED_MIN, BALL_SPEED_MAX = 3, 6
FPS = 60
SMOOTHING = 0.25

pygame.init()
screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("🎃 Halloween Ultra Catch - 12 Powerups")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 34)
font_big = pygame.font.SysFont(None, 72)

# Colors (Halloween)
COLOR_BG = (12, 6, 28)
COLOR_PANEL = (20, 12, 40)
COLOR_TEXT = (255, 180, 80)
COLOR_PADDLE = (70, 10, 10)

# ---------------- Mediapipe Init ----------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5
)

# ---------------- Utility functions ----------------
def draw_text(s, t, x, y, c=COLOR_TEXT):
    img = font.render(t, True, c)
    s.blit(img, (x, y))

def draw_center_text(s, t, x, y, fnt, c=(255,255,255)):
    img = fnt.render(t, True, c)
    rect = img.get_rect(center=(x,y))
    s.blit(img, rect)

# ---------------- Particle System ----------------
class Particle:
    def __init__(self, x, y, vx, vy, life, color, size=4):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.life = life
        self.color = color
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.08  # gravity like
        self.life -= 1

    def draw(self, s):
        if self.life > 0:
            pygame.draw.circle(s, self.color, (int(self.x), int(self.y)), self.size)

particles = []

def spawn_particles(x, y, n, color_range, speed=3, life_range=(20,40), size=3):
    for _ in range(n):
        vx = random.uniform(-speed, speed)
        vy = random.uniform(-speed, -1)
        life = random.randint(*life_range)
        c = (random.randint(*color_range[0]), random.randint(*color_range[1]), random.randint(*color_range[2]))
        particles.append(Particle(x, y, vx, vy, life, c, size))

# ---------------- Ball & Powerup definitions ----------------
def spawn_ball():
    x = random.randint(BALL_RADIUS, WIN_W - BALL_RADIUS)
    y = -BALL_RADIUS - random.randint(0,200)
    vy = random.uniform(BALL_SPEED_MIN, BALL_SPEED_MAX)
    color = (255, random.randint(80,160), 0)  # pumpkin orange
    return {"x": x, "y": y, "vy": vy, "color": color, "radius": BALL_RADIUS, "frozen": False}

# Powerup types (12):
POWERUP_TYPES = [
    "PADDLE_GROW",     # bigger paddle
    "PADDLE_SHRINK",   # smaller paddle
    "SLOW_MOTION",     # slow time
    "MAGNET",          # attract balls
    "ANGRY_GHOST",     # spawns enemy ghost
    "HELL_BOMB",       # explosive bomb effect
    "WITCH",           # bless or curse
    "FREEZE",          # freeze next ball
    "TIME_REWIND",     # restore last missed ball
    "SHIELD",          # one-ball shield (prevents life loss)
    "DOUBLE_POINTS",   # double score for duration
    "MULTI_BALL"       # spawn extra balls
]

def spawn_powerup():
    t = random.choice(POWERUP_TYPES)
    x = random.randint(40, WIN_W - 40)
    y = -20
    vy = random.uniform(2.0, 3.5)
    # simple color by type
    color_map = {
        "PADDLE_GROW": (255,140,0),
        "PADDLE_SHRINK": (130,30,200),
        "SLOW_MOTION": (120,200,255),
        "MAGNET": (180,100,255),
        "ANGRY_GHOST": (200,200,255),
        "HELL_BOMB": (220,40,40),
        "WITCH": (90,0,140),
        "FREEZE": (160,220,255),
        "TIME_REWIND": (100,230,200),
        "SHIELD": (200,200,100),
        "DOUBLE_POINTS": (255,215,0),
        "MULTI_BALL": (255,100,200)
    }
    return {"type": t, "x": x, "y": y, "vy": vy, "color": color_map[t], "angle": 0}

# ---------------- Game State ----------------
class ActiveEffect:
    def __init__(self, name, duration, params=None):
        self.name = name
        self.end_time = time.time() + duration
        self.params = params or {}
    def remaining(self):
        return max(0, self.end_time - time.time())
    def active(self):
        return self.remaining() > 0

# history for time rewind
ball_history = deque(maxlen=8)  # store last missed balls

# ---------------- Enemy: Angry Ghost ----------------
class AngryGhost:
    def __init__(self):
        self.x = random.randint(50, WIN_W-50)
        self.y = -80
        self.vx = random.choice([-2,2])
        self.vy = 2.2
        self.alive = True
        self.angle = 0
    def update(self):
        if not self.alive: return
        self.x += self.vx
        self.y += self.vy
        # bounce sides
        if self.x < 40 or self.x > WIN_W-40:
            self.vx *= -1
        self.angle = (self.angle + 5) % 360
    def draw(self, s):
        if not self.alive: return
        # simple ghost: circle + tail
        pygame.draw.ellipse(s, (200,220,255), (int(self.x)-28, int(self.y)-18, 56, 44))
        # eyes
        pygame.draw.circle(s, (40,40,80), (int(self.x)-10, int(self.y)-4), 4)
        pygame.draw.circle(s, (40,40,80), (int(self.x)+10, int(self.y)-4), 4)
ghosts = []

# ---------------- Main game loop ----------------
def get_hand_position(cap):
    ret, frame = cap.read()
    if not ret:
        return None
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    r = hands.process(rgb)
    if not r.multi_hand_landmarks:
        return None
    lm = r.multi_hand_landmarks[0].landmark[8]
    return int(lm.x * WIN_W), int(lm.y * WIN_H)

def game_loop():
    cap = cv2.VideoCapture(0)
    balls = [spawn_ball() for _ in range(4)]
    powerups = []
    score = 0
    lives = 5
    paddle_x = WIN_W // 2
    paddle_y = WIN_H - 90
    smoothed_x = paddle_x
    last_spawn = time.time()
    spawn_interval = 1.0
    last_power_spawn = time.time()
    power_spawn_interval = 4.0

    active_effects = []
    shield_active = False
    double_points = False
    magnet_strength = 0.0
    slow_factor = 1.0
    frozen_next = False
    last_missed = None

    global ball_history, ghosts

    # paddle dynamic size
    current_paddle_w = PADDLE_W
    base_paddle_w = PADDLE_W

    # store recent balls for rewind (copy positions & colors)
    ball_history.clear()

    running = True
    while running:
        # --- Input / hand tracking
        hand = get_hand_position(cap)
        if hand:
            tx = hand[0]
            smoothed_x = int(smoothed_x * (1 - SMOOTHING) + tx * SMOOTHING)
            paddle_x = np.clip(smoothed_x, current_paddle_w//2, WIN_W - current_paddle_w//2)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()

        # --- Update balls
        for b in balls:
            if not b["frozen"]:
                b["y"] += b["vy"] * slow_factor
            else:
                # small wobble
                b["y"] += 0.25

            # magnet effect: pull x towards paddle_x
            if magnet_strength > 0:
                dx = paddle_x - b["x"]
                b["x"] += dx * magnet_strength * 0.02

        # --- Spawn new ball gradually
        if time.time() - last_spawn > spawn_interval:
            balls.append(spawn_ball())
            last_spawn = time.time()
            # difficulty escalate slightly
            if spawn_interval > 0.45:
                spawn_interval = max(0.45, spawn_interval - 0.005)

        # --- Spawn powerups occasionally
        if time.time() - last_power_spawn > power_spawn_interval:
            powerups.append(spawn_powerup())
            last_power_spawn = time.time()
            # make powerups more frequent over time
            power_spawn_interval = max(2.0, power_spawn_interval - 0.02)

        # --- Update powerup positions (rotate animation)
        for pu in powerups:
            pu["y"] += pu["vy"]
            pu["angle"] = (pu["angle"] + 3) % 360

        # --- Update ghosts
        for g in ghosts:
            g.update()

        # --- Collisions with paddle
        paddle_rect = pygame.Rect(0,0,int(current_paddle_w),PADDLE_H)
        paddle_rect.center = (int(paddle_x), paddle_y)

        for b in balls[:]:
            # Collision check: bottom crossing / paddle
            if b["y"] + b["radius"] >= paddle_y - PADDLE_H//2:
                dist_x = abs(b["x"] - paddle_x)
                if dist_x <= (current_paddle_w//2 + b["radius"]):
                    # caught
                    pts = 1
                    if double_points: pts *= 2
                    score += pts
                    # spawn particles
                    spawn_particles(b["x"], b["y"], 18, ((240,255),(90,160),(0,60)), speed=4, life_range=(18,36), size=4)
                    # if freeze active -> break ball into shards and create more small balls
                    if frozen_next:
                        # break animation
                        for _ in range(8):
                            particles.append(Particle(b["x"], b["y"], random.uniform(-4,4), random.uniform(-6,-1), random.randint(15,30), (180,230,255), 3))
                        frozen_next = False
                    balls.remove(b)
                    # keep history of caught? not necessary
                else:
                    # missed — ball goes past paddle bottom -> life loss unless shield
                    if b["y"] - b["radius"] > WIN_H:
                        # record missed ball to history (for rewind)
                        ball_history.append({"x": b["x"], "color": b["color"], "radius": b["radius"]})
                        last_missed = time.time()
                        if shield_active:
                            # shield consumes and prevents life loss
                            shield_active = False
                            # particle shield pop
                            spawn_particles(paddle_x, paddle_y, 30, ((220,255),(120,180),(0,40)), speed=3, life_range=(15,28), size=4)
                        else:
                            lives -= 1
                            # ghost particle scream
                            spawn_particles(b["x"], WIN_H-10, 20, ((180,200),(180,200),(250,255)), speed=2, life_range=(20,40), size=3)
                        balls.remove(b)

        # --- Pickup powerups by paddle
        for pu in powerups[:]:
            # simple collide if Y near paddle and X close
            if pu["y"] >= paddle_y - 60 and abs(pu["x"] - paddle_x) <= (current_paddle_w//2 + 20):
                # activate
                typ = pu["type"]
                # small pickup animation
                for _ in range(14):
                    particles.append(Particle(pu["x"] + random.uniform(-20,20), pu["y"] + random.uniform(-10,10), random.uniform(-3,3), random.uniform(-6,-1), random.randint(12,28), pu["color"], 3))

                if typ == "PADDLE_GROW":
                    active_effects.append(ActiveEffect("PADDLE_GROW", 10, {"scale":1.5}))
                    current_paddle_w = base_paddle_w * 1.5

                elif typ == "PADDLE_SHRINK":
                    active_effects.append(ActiveEffect("PADDLE_SHRINK", 10, {"scale":0.7}))
                    current_paddle_w = int(base_paddle_w * 0.7)

                elif typ == "SLOW_MOTION":
                    active_effects.append(ActiveEffect("SLOW_MOTION", 6, {"factor":0.45}))
                    slow_factor = 0.45

                elif typ == "MAGNET":
                    active_effects.append(ActiveEffect("MAGNET", 8, {"strength":0.9}))
                    magnet_strength = 0.9

                elif typ == "ANGRY_GHOST":
                    # spawn a ghost enemy
                    g = AngryGhost()
                    ghosts.append(g)

                elif typ == "HELL_BOMB":
                    # immediate explosion: spawn multiple balls (as hazard) and shake
                    for _ in range(6):
                        nb = spawn_ball()
                        nb["x"] = random.randint(40, WIN_W-40)
                        nb["y"] = -10
                        nb["vy"] = random.uniform(5,8)
                        balls.append(nb)
                    # heavy particle red
                    spawn_particles(paddle_x, paddle_y-30, 40, ((220,255),(20,60),(20,60)), speed=6, life_range=(30,45), size=4)

                elif typ == "WITCH":
                    # random bless or curse
                    if random.random() < 0.6:
                        # bless
                        active_effects.append(ActiveEffect("WITCH_BLESS", 6, {"life":2, "auto_catch":True}))
                        lives = min(9, lives + 2)
                        # auto catch implemented via magnet + short glory
                        magnet_strength = 0.95
                    else:
                        # curse
                        active_effects.append(ActiveEffect("WITCH_CURSE", 8, {"speed_mult":1.5}))
                        # increase speeds temporarily
                        for b in balls:
                            b["vy"] *= 1.4

                elif typ == "FREEZE":
                    # freeze next collision ball
                    frozen_next = True

                elif typ == "TIME_REWIND":
                    # restore last missed if exists
                    if ball_history:
                        val = ball_history.pop()
                        balls.append({"x": val["x"], "y": -30, "vy": random.uniform(2,5), "color": val["color"], "radius": val["radius"], "frozen": False})
                        # particles to indicate time warp
                        spawn_particles(val["x"], 40, 18, ((100,200),(200,255),(200,255)), speed=3, life_range=(20,35), size=4)

                elif typ == "SHIELD":
                    active_effects.append(ActiveEffect("SHIELD", 15, {}))
                    shield_active = True

                elif typ == "DOUBLE_POINTS":
                    active_effects.append(ActiveEffect("DOUBLE_POINTS", 10, {}))
                    double_points = True

                elif typ == "MULTI_BALL":
                    # spawn extra smaller balls (bonuses)
                    for _ in range(3):
                        nb = spawn_ball()
                        nb["x"] = random.randint(60, WIN_W-60)
                        nb["y"] = -random.randint(10,80)
                        nb["vy"] = random.uniform(3,7)
                        balls.append(nb)

                # remove powerup
                powerups.remove(pu)

        # --- Ghost interactions: ghost can deflect balls / be shot by paddle (if contact)
        for g in ghosts[:]:
            if not g.alive: 
                ghosts.remove(g); continue
            # deflect nearest ball if close
            for b in balls:
                if abs(b["x"] - g.x) < 40 and abs(b["y"] - g.y) < 40 and b["y"] < g.y:
                    b["vy"] = -abs(b["vy"]) * 0.8
            # if ghost touches paddle -> cause shake and small penalty (temporary shrink)
            if abs(g.x - paddle_x) < current_paddle_w//2 and abs(g.y - paddle_y) < 40:
                # ghost hits paddle => vanish and cause effect
                g.alive = False
                active_effects.append(ActiveEffect("GHOST_HIT_SHRINK", 3, {"scale":0.6}))
                current_paddle_w = int(base_paddle_w * 0.6)
                spawn_particles(g.x, g.y, 30, ((200,230),(200,230),(255,255)), speed=3, life_range=(16,32), size=3)

        # --- Update particles
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

        # --- Manage active effects and expiration
        # reset flags then re-apply based on active effects
        magnet_strength = 0.0
        slow_factor = 1.0
        double_points = any(e.name == "DOUBLE_POINTS" and e.active() for e in active_effects)
        shield_active = any(e.name == "SHIELD" and e.active() for e in active_effects)

        # paddle size resets to base unless modified
        current_paddle_w = base_paddle_w

        # evaluate others
        for e in active_effects[:]:
            if not e.active():
                active_effects.remove(e)
                # on-expire behaviours
                if e.name == "SLOW_MOTION":
                    slow_factor = 1.0
                if e.name == "PADDLE_GROW" or e.name == "PADDLE_SHRINK" or e.name == "GHOST_HIT_SHRINK":
                    current_paddle_w = base_paddle_w
                continue
            # apply active ones
            if e.name == "PADDLE_GROW":
                current_paddle_w = int(base_paddle_w * e.params.get("scale",1.5))
            if e.name == "PADDLE_SHRINK":
                current_paddle_w = int(base_paddle_w * e.params.get("scale",0.7))
            if e.name == "SLOW_MOTION":
                slow_factor = e.params.get("factor", 0.5)
            if e.name == "MAGNET":
                magnet_strength = e.params.get("strength", 0.85)
            if e.name == "WITCH_BLESS":
                # small aura
                pass
            if e.name == "WITCH_CURSE":
                # curses were applied immediately to ball speeds
                pass

        # --- Draw everything ---
        screen.fill(COLOR_BG)
        # HUD panel top
        pygame.draw.rect(screen, COLOR_PANEL, (0,0,WIN_W,80))
        draw_text(screen, f"🎃 Score: {score}", 18, 18, (255,180,80))
        draw_text(screen, f"💀 Lives: {lives}", 18, 48, (255,120,120))

        # Draw active effects timers UI
        ax = WIN_W - 250
        ay = 18
        draw_text(screen, "Effects:", ax, ay, (220,220,220))
        i = 0
        for e in active_effects:
            # small bar
            if i >= 6: break
            w = max(0, int(200 * (e.remaining() / ( (e.end_time - (e.end_time - e.remaining())) if e.remaining() else 1 ))))
            pygame.draw.rect(screen, (80,80,120), (ax, ay+30 + i*22, 210, 16), border_radius=6)
            # color by effect
            col = (180,120,255) if "PADDLE" in e.name else (120,220,255) if "SLOW" in e.name else (255,180,80)
            pygame.draw.rect(screen, col, (ax, ay+30 + i*22, w, 16), border_radius=6)
            draw_text(screen, e.name.replace("_"," "), ax+4, ay+30 + i*22 -1, (10,10,10))
            i += 1

        # Draw paddle (coffin style)
        coffin = pygame.Rect(0,0,int(current_paddle_w), PADDLE_H)
        coffin.center = (int(paddle_x), paddle_y)
        pygame.draw.rect(screen, COLOR_PADDLE, coffin, border_radius=20)
        # little cross decoration
        pygame.draw.line(screen, (40,10,10), (coffin.centerx, coffin.top+4), (coffin.centerx, coffin.bottom-4), 2)
        pygame.draw.line(screen, (40,10,10), (coffin.left+6, coffin.centery), (coffin.right-6, coffin.centery), 2)

        # Draw balls
        for b in balls:
            # radius scaling if frozen
            r = b["radius"]
            if b["frozen"]:
                pygame.draw.circle(screen, (180,230,255), (int(b["x"]), int(b["y"])), r+2)
                pygame.draw.circle(screen, (120,180,220), (int(b["x"]), int(b["y"])), r, 2)
            else:
                pygame.draw.circle(screen, b["color"], (int(b["x"]), int(b["y"])), r)
                pygame.draw.circle(screen, (20,10,0), (int(b["x"]), int(b["y"])), r, 2)

        # Draw powerups (animated)
        for pu in powerups:
            ang = pu["angle"]
            # rotating square icon
            s = 28
            surf = pygame.Surface((s,s), pygame.SRCALPHA)
            pygame.draw.rect(surf, pu["color"] + (220,), (0,0,s,s), border_radius=6)
            # small label char
            label = font.render(pu["type"][0], True, (10,10,10))
            surf.blit(label, (s//3, s//6))
            # rotate
            rot = pygame.transform.rotate(surf, ang)
            rx = rot.get_rect(center=(int(pu["x"]), int(pu["y"])))
            screen.blit(rot, rx.topleft)
            # tiny glow
            pygame.draw.circle(screen, (255,255,255), (int(pu["x"]), int(pu["y"])), 2)

        # Draw ghosts
        for g in ghosts:
            g.draw(screen)

        # Draw particles
        for p in particles:
            p.draw(screen)

        # powerup hint
        draw_text(screen, "Grab falling items with your hand to activate powerups", 260, 48, (200,200,220))

        # Check game over
        if lives <= 0:
            cap.release()
            return score

        pygame.display.flip()
        clock.tick(FPS)

def game_over_screen(score):
    cap = cv2.VideoCapture(0)
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        screen.fill((12,0,0))
        draw_center_text(screen, "GAME OVER", WIN_W//2, 150, font_big, (255,60,60))
        draw_center_text(screen, f"Final Score: {score}", WIN_W//2, 260, font, (255,200,120))
        draw_center_text(screen, "Raise hand to restart — or press ESC to exit", WIN_W//2, 360, font, (220,220,255))
        # detect hand to restart
        hand = get_hand_position(cap)
        keys = pygame.key.get_pressed()
        if hand: 
            cap.release()
            return "restart"
        if keys[pygame.K_ESCAPE]:
            cap.release()
            return "exit"
        pygame.display.flip()
        clock.tick(30)

# ---------------- Main loop ----------------
while True:
    s = game_loop()
    action = game_over_screen(s)
    if action == "exit":
        pygame.quit()
        sys.exit()
# ---------------- Made by Asma & Mooud ----------------
