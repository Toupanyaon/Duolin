# Duolingo (mini) - a language learning game made with Pygame
# Run:  python main.py

import pygame
import json
import os
import random
import hashlib
import time
from datetime import date, timedelta
from questions import LESSONS

WIDTH, HEIGHT = 800, 600
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save_data.json")
MAX_HEARTS = 3
PRACTICE_GOAL = 5  # correct answers in Practice Mode to get 1 heart back

WHITE = (255, 255, 255)
BLACK = (60, 60, 60)
GREEN = (88, 204, 2)
RED = (255, 75, 75)
BLUE = (28, 176, 246)
GRAY = (229, 229, 229)
ORANGE = (255, 150, 0)
GOLD = (255, 200, 0)
LIGHT_GREEN = (215, 255, 184)
LIGHT_RED = (255, 223, 224)

# Daily quests: (text, key in player["daily"], goal)
QUESTS = [
    ("Earn 50 XP", "xp", 50),
    ("Get 10 correct answers", "correct", 10),
    ("Finish 1 lesson", "lessons", 1),
]

# Achievements: (name, description, condition)
ACHIEVEMENTS = [
    ("First Lesson", "Finish your first lesson", lambda p: len(p["completed"]) >= 1),
    ("XP Hunter", "Reach 100 XP", lambda p: p["xp"] >= 100),
    ("On Fire", "Reach a 3 day streak", lambda p: p["streak"] >= 3),
    ("Perfect!", "Finish a lesson with no mistakes", lambda p: p["perfect"]),
    ("Comeback", "Win back a heart in Practice Mode", lambda p: p["restored"]),
    ("Quest Master", "Complete all daily quests in one day",
     lambda p: all(p["daily"][key] >= goal for _, key, goal in QUESTS)),
    ("Graduate", "Finish every lesson", lambda p: len(p["completed"]) == len(LESSONS)),
]


# ---------------- Save / load ----------------

def today():
    return date.today().isoformat()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def new_player(password):
    return {
        "password": hash_password(password),
        "xp": 0,
        "xp_time": time.time(),      # when the player reached their current XP
        "streak": 0,
        "last_play": "",
        "hearts": MAX_HEARTS,
        "hearts_date": today(),
        "wrong": [],                 # ids of questions answered wrong ("lesson-question")
        "practice_correct": 0,
        "progress": {},              # lesson number -> question to resume from
        "completed": [],
        "achievements": [],
        "perfect": False,
        "restored": False,
        "daily": {"date": today(), "xp": 0, "correct": 0, "lessons": 0},
    }


# ---------------- Game ----------------

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Duolingo")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24)
        self.small = pygame.font.SysFont("arial", 18)
        self.big = pygame.font.SysFont("arial", 42, bold=True)
        self.tiny = pygame.font.SysFont("arial", 14)

        self.data = load_data()
        self.user = None
        self.state = "login"
        self.buttons = []
        self.message = ""
        self.popup = ""
        self.popup_time = 0

        # login screen
        self.name_text = ""
        self.pass_text = ""
        self.active = "name"

        # question screen
        self.mode = "lesson"         # "lesson" or "practice"
        self.lesson = 0
        self.q_index = 0
        self.qid = ""
        self.question = None
        self.options = []
        self.selected = None
        self.pool = []
        self.chosen = []
        self.feedback = None         # None, "correct" or "wrong"
        self.mistakes = 0
        self.resumed = False

    @property
    def player(self):
        return self.data[self.user]

    # ---------- drawing helpers ----------

    def text(self, msg, x, y, font=None, color=BLACK, center=False):
        img = (font or self.font).render(str(msg), True, color)
        rect = img.get_rect(center=(x, y)) if center else img.get_rect(topleft=(x, y))
        self.screen.blit(img, rect)

    def button(self, label, rect, action, color=GREEN, text_color=WHITE, font=None):
        rect = pygame.Rect(rect)
        if rect.collidepoint(pygame.mouse.get_pos()):
            color = tuple(max(c - 25, 0) for c in color)
        pygame.draw.rect(self.screen, color, rect, border_radius=12)
        self.text(label, rect.centerx, rect.centery, font, text_color, center=True)
        self.buttons.append((rect, action))

    def draw_hearts(self, x, y):
        for i in range(MAX_HEARTS):
            color = RED if i < self.player["hearts"] else GRAY
            pygame.draw.circle(self.screen, color, (x + i * 30, y), 11)

    def draw_header(self):
        p = self.player
        pygame.draw.rect(self.screen, GRAY, (0, 0, WIDTH, 60))
        self.text(self.user, 20, 18, color=BLUE)
        self.text(f"Level {p['xp'] // 100 + 1}", 220, 18)
        self.text(f"XP {p['xp']}", 350, 18, color=GOLD)
        self.text(f"Streak {p['streak']} days", 470, 18, color=ORANGE)
        self.draw_hearts(700, 30)

    def notify(self, msg):
        self.popup = msg
        self.popup_time = time.time()

    def change_state(self, state):
        self.state = state
        self.message = ""

    # ---------- main loop ----------

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_data(self.data)
                    pygame.quit()
                    return
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for rect, action in self.buttons:
                        if rect.collidepoint(event.pos):
                            action()
                            break
                if event.type == pygame.KEYDOWN and self.state == "login":
                    self.login_keys(event)

            self.screen.fill(WHITE)
            self.buttons = []
            getattr(self, "draw_" + self.state)()

            if time.time() - self.popup_time < 2.5:
                pygame.draw.rect(self.screen, GOLD, (150, 10, 500, 45), border_radius=12)
                self.text(self.popup, WIDTH // 2, 32, color=BLACK, center=True)

            pygame.display.flip()
            self.clock.tick(30)

    # ---------- login ----------

    def login_keys(self, event):
        field = "name_text" if self.active == "name" else "pass_text"
        value = getattr(self, field)
        if event.key == pygame.K_TAB:
            self.active = "pass" if self.active == "name" else "name"
        elif event.key == pygame.K_RETURN:
            self.login()
        elif event.key == pygame.K_BACKSPACE:
            setattr(self, field, value[:-1])
        elif event.unicode.isprintable() and event.unicode and len(value) < 15:
            setattr(self, field, value + event.unicode)

    def set_active(self, field):
        self.active = field

    def draw_login(self):
        self.text("Duolingo", WIDTH // 2, 100, self.big, GREEN, center=True)
        self.text("Learn Spanish!", WIDTH // 2, 150, self.small, center=True)

        boxes = [("Player name", "name", self.name_text, 220),
                 ("Password", "pass", "*" * len(self.pass_text), 310)]
        for label, field, value, y in boxes:
            self.text(label, 250, y - 28, self.small)
            rect = pygame.Rect(250, y, 300, 45)
            border = BLUE if self.active == field else GRAY
            pygame.draw.rect(self.screen, border, rect, 3, border_radius=8)
            self.text(value, rect.x + 10, rect.y + 9)
            self.buttons.append((rect, lambda f=field: self.set_active(f)))

        self.button("Log in", (250, 390, 140, 50), self.login)
        self.button("Register", (410, 390, 140, 50), self.register, BLUE)
        self.text(self.message, WIDTH // 2, 480, self.small, RED, center=True)
        self.text("TAB = switch box    ENTER = log in", WIDTH // 2, 560, self.small, center=True)

    def login(self):
        name, pw = self.name_text.strip(), self.pass_text
        if name not in self.data:
            self.message = "Player not found. Click Register to create one."
        elif self.data[name]["password"] != hash_password(pw):
            self.message = "Wrong password!"
        else:
            self.enter_game(name)

    def register(self):
        name, pw = self.name_text.strip(), self.pass_text
        if not name or not pw:
            self.message = "Please type a name and a password."
        elif name in self.data:
            self.message = "This name is already taken."
        else:
            self.data[name] = new_player(pw)
            save_data(self.data)
            self.enter_game(name)

    def enter_game(self, name):
        self.user = name
        self.pass_text = ""
        self.refresh_day()
        self.change_state("menu")

    def logout(self):
        save_data(self.data)
        self.user = None
        self.change_state("login")

    # ---------- daily things ----------

    def refresh_day(self):
        p = self.player
        if p["hearts_date"] != today():          # new day = full hearts
            p["hearts"] = MAX_HEARTS
            p["hearts_date"] = today()
        if p["daily"]["date"] != today():        # new day = new quests
            p["daily"] = {"date": today(), "xp": 0, "correct": 0, "lessons": 0}
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        if p["last_play"] not in ("", today(), yesterday):  # missed a day
            p["streak"] = 0
        save_data(self.data)

    def update_streak(self):
        p = self.player
        if p["last_play"] == today():
            return
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        p["streak"] = p["streak"] + 1 if p["last_play"] == yesterday else 1
        p["last_play"] = today()

    def add_xp(self, amount):
        p = self.player
        p["xp"] += amount
        p["xp_time"] = time.time()
        p["daily"]["xp"] += amount

    def check_achievements(self):
        p = self.player
        for name, _, condition in ACHIEVEMENTS:
            if name not in p["achievements"] and condition(p):
                p["achievements"].append(name)
                self.notify(f"Achievement unlocked: {name}!")

    # ---------- menu ----------

    def draw_menu(self):
        self.draw_header()
        p = self.player
        self.text("Lessons", 60, 90, self.big)
        for i, lesson in enumerate(LESSONS):
            label = f"{i + 1}. {lesson['name']}"
            color = GREEN
            if str(i) in p["progress"]:
                label += "  (Resume)"
                color = ORANGE
            elif i in p["completed"]:
                label += "  (Done)"
                color = BLUE
            self.button(label, (60, 160 + i * 80, 380, 60), lambda i=i: self.start_lesson(i), color)

        self.button("Practice Mode", (500, 160, 240, 55), self.start_practice, ORANGE)
        self.button("Quests & Badges", (500, 235, 240, 55), lambda: self.change_state("quests"), BLUE)
        self.button("Leaderboard", (500, 310, 240, 55), lambda: self.change_state("leaderboard"), BLUE)
        self.button("Log out", (500, 385, 240, 55), self.logout, GRAY, BLACK)

        self.text(f"Mistakes to practice: {len(p['wrong'])}", 500, 460, self.small)
        self.text(f"Practice: {p['practice_correct']}/{PRACTICE_GOAL} to get a heart", 500, 490, self.small)
        self.text(self.message, 60, 420, self.small, RED)

    # ---------- lesson / practice ----------

    def start_lesson(self, i):
        self.refresh_day()
        if self.player["hearts"] == 0:
            self.change_state("no_hearts")
            return
        self.mode = "lesson"
        self.lesson = i
        self.q_index = self.player["progress"].get(str(i), 0)
        self.resumed = self.q_index > 0
        self.mistakes = 0
        if self.q_index >= len(LESSONS[i]["questions"]):
            self.finish_lesson()
            return
        self.load_question()
        self.change_state("question")

    def start_practice(self):
        self.mode = "practice"
        self.load_question()
        self.change_state("question")

    def load_question(self):
        if self.mode == "lesson":
            self.qid = f"{self.lesson}-{self.q_index}"
        else:
            # practice wrong questions first, if none left use any question
            ids = self.player["wrong"] or [f"{l}-{q}" for l in range(len(LESSONS))
                                           for q in range(len(LESSONS[l]["questions"]))]
            self.qid = random.choice(ids)
        l, q = map(int, self.qid.split("-"))
        self.question = LESSONS[l]["questions"][q]

        self.feedback = None
        self.selected = None
        self.chosen = []
        if self.question["type"] == "choice":
            self.options = random.sample(self.question["options"], len(self.question["options"]))
        else:
            self.pool = self.question["answer"] + self.question.get("extra", [])
            random.shuffle(self.pool)

    def quit_question(self):
        if self.mode == "lesson" and self.q_index > 0:
            self.player["progress"][str(self.lesson)] = self.q_index
        save_data(self.data)
        self.change_state("menu")

    def select_option(self, option):
        if self.feedback is None:
            self.selected = option

    def pick_word(self, i):
        if self.feedback is None:
            self.chosen.append(self.pool.pop(i))

    def remove_word(self, i):
        if self.feedback is None:
            self.pool.append(self.chosen.pop(i))

    def draw_tiles(self, words, y, on_click):
        x = 100
        for i, word in enumerate(words):
            w = self.font.size(word)[0] + 30
            self.button(word, (x, y, w, 50), lambda i=i: on_click(i), GRAY, BLACK)
            x += w + 12

    def draw_question(self):
        p = self.player
        q = self.question

        # top bar
        self.button("X", (20, 15, 45, 40), self.quit_question, GRAY, BLACK)
        if self.mode == "lesson":
            total = len(LESSONS[self.lesson]["questions"])
            pygame.draw.rect(self.screen, GRAY, (90, 27, 560, 16), border_radius=8)
            pygame.draw.rect(self.screen, GREEN, (90, 27, 560 * self.q_index // total, 16), border_radius=8)
        else:
            self.text(f"Practice Mode  {p['practice_correct']}/{PRACTICE_GOAL} for a heart",
                      90, 20, color=ORANGE)
        self.draw_hearts(700, 35)

        self.text(q["question"], WIDTH // 2, 120, self.font, center=True)

        if q["type"] == "choice":
            for i, option in enumerate(self.options):
                color = BLUE if option == self.selected else GRAY
                text_color = WHITE if option == self.selected else BLACK
                self.button(option, (250, 170 + i * 65, 300, 52),
                            lambda o=option: self.select_option(o), color, text_color)
        else:
            pygame.draw.line(self.screen, GRAY, (100, 290), (700, 290), 2)
            self.draw_tiles(self.chosen, 230, self.remove_word)
            self.draw_tiles(self.pool, 340, self.pick_word)

        # bottom bar
        if self.feedback is None:
            ready = self.selected is not None or len(self.chosen) > 0
            self.button("Check", (300, 500, 200, 55), self.check_answer, GREEN if ready else GRAY)
        else:
            correct = self.feedback == "correct"
            pygame.draw.rect(self.screen, LIGHT_GREEN if correct else LIGHT_RED, (0, 470, WIDTH, 130))
            if correct:
                self.text("Correct!  +10 XP", 40, 485, color=GREEN)
            else:
                answer = q["answer"] if q["type"] == "choice" else " ".join(q["answer"])
                self.text("Wrong!  Correct answer: " + answer, 40, 485, color=RED)
            self.button("Continue", (560, 520, 200, 55), self.next_question, GREEN if correct else RED)

    def check_answer(self):
        q = self.question
        if q["type"] == "choice":
            if self.selected is None:
                return
            correct = self.selected == q["answer"]
        else:
            if not self.chosen:
                return
            correct = self.chosen == q["answer"]

        p = self.player
        self.update_streak()
        if correct:
            self.feedback = "correct"
            self.add_xp(10)
            p["daily"]["correct"] += 1
            if self.mode == "practice":
                if self.qid in p["wrong"]:
                    p["wrong"].remove(self.qid)
                if p["hearts"] < MAX_HEARTS:
                    p["practice_correct"] += 1
                    if p["practice_correct"] >= PRACTICE_GOAL:
                        p["practice_correct"] = 0
                        p["hearts"] += 1
                        p["restored"] = True
                        self.notify("+1 Heart! Go back and resume your lesson")
        else:
            self.feedback = "wrong"
            if self.qid not in p["wrong"]:
                p["wrong"].append(self.qid)
            if self.mode == "lesson":
                p["hearts"] -= 1
                self.mistakes += 1

        self.check_achievements()
        save_data(self.data)

    def next_question(self):
        p = self.player
        if self.mode == "practice":
            self.load_question()
            return
        self.q_index += 1
        if p["hearts"] == 0:
            p["progress"][str(self.lesson)] = self.q_index   # remember where we stopped
            save_data(self.data)
            self.change_state("no_hearts")
        elif self.q_index >= len(LESSONS[self.lesson]["questions"]):
            self.finish_lesson()
        else:
            self.load_question()

    def finish_lesson(self):
        p = self.player
        self.add_xp(20)
        p["daily"]["lessons"] += 1
        p["progress"].pop(str(self.lesson), None)
        if self.lesson not in p["completed"]:
            p["completed"].append(self.lesson)
        if self.mistakes == 0 and not self.resumed:
            p["perfect"] = True
        self.check_achievements()
        save_data(self.data)
        self.change_state("lesson_done")

    def draw_lesson_done(self):
        self.text("Lesson Complete!", WIDTH // 2, 200, self.big, GREEN, center=True)
        self.text("+20 XP bonus", WIDTH // 2, 270, self.font, GOLD, center=True)
        self.text(f"Total XP: {self.player['xp']}", WIDTH // 2, 320, center=True)
        self.button("Continue", (300, 420, 200, 55), lambda: self.change_state("menu"))

    def draw_no_hearts(self):
        self.text("Out of hearts!", WIDTH // 2, 180, self.big, RED, center=True)
        self.text("Practice your mistakes to win hearts back.", WIDTH // 2, 250, center=True)
        self.text(f"{PRACTICE_GOAL} correct answers = 1 heart", WIDTH // 2, 290, self.small, center=True)
        self.button("Practice Mode", (280, 360, 240, 55), self.start_practice, ORANGE)
        self.button("Back to Menu", (280, 435, 240, 55), lambda: self.change_state("menu"), GRAY, BLACK)

    # ---------- leaderboard ----------

    def draw_leaderboard(self):
        self.text("Leaderboard", WIDTH // 2, 50, self.big, BLUE, center=True)
        # rank by XP, then streak, then who reached that XP first
        ranking = sorted(self.data.items(),
                         key=lambda item: (-item[1]["xp"], -item[1]["streak"], item[1]["xp_time"]))
        headers = [("Rank", 80), ("Player", 180), ("XP", 420), ("Level", 520), ("Streak", 630)]
        for title, x in headers:
            self.text(title, x, 100, color=BLUE)
        for i, (name, p) in enumerate(ranking[:10]):
            y = 140 + i * 36
            if name == self.user:
                pygame.draw.rect(self.screen, LIGHT_GREEN, (60, y - 4, 680, 34), border_radius=6)
            for value, x in zip([i + 1, name, p["xp"], p["xp"] // 100 + 1, p["streak"]],
                                [80, 180, 420, 520, 630]):
                self.text(value, x, y)
        self.button("Back", (300, 530, 200, 50), lambda: self.change_state("menu"), GRAY, BLACK)

    # ---------- quests & achievements ----------

    def draw_quests(self):
        p = self.player
        self.text("Daily Quests", 60, 30, self.big, ORANGE)
        for i, (text, key, goal) in enumerate(QUESTS):
            y = 95 + i * 50
            value = min(p["daily"][key], goal)
            self.text(f"{text}  ({value}/{goal})", 60, y, self.small)
            pygame.draw.rect(self.screen, GRAY, (420, y + 2, 300, 18), border_radius=9)
            pygame.draw.rect(self.screen, GOLD, (420, y + 2, 300 * value // goal, 18), border_radius=9)

        self.text("Achievements", 60, 250, self.big, BLUE)
        for i, (name, desc, _) in enumerate(ACHIEVEMENTS):
            x = 60 + (i % 2) * 360
            y = 315 + (i // 2) * 50
            unlocked = name in p["achievements"]
            pygame.draw.circle(self.screen, GOLD if unlocked else GRAY, (x + 15, y + 18), 15)
            self.text(name, x + 40, y, self.small, BLACK if unlocked else GRAY)
            self.text(desc, x + 40, y + 20, self.tiny, BLACK if unlocked else GRAY)
        self.button("Back", (300, 530, 200, 50), lambda: self.change_state("menu"), GRAY, BLACK)


if __name__ == "__main__":
    Game().run()
