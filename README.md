# Duolingo (mini) - Pygame

## How to run
```
pip install pygame
python main.py
```

## Files
- `main.py`       - the game (screens, rules, saving)
- `questions.py`  - lesson questions (Choice + Word ordering)
- `save_data.json` - created automatically, stores every player's progress

## Rules
- Register / log in with a player name and password (password is saved as a SHA-256 hash)
- 3 hearts per day, a wrong answer in a lesson costs 1 heart
- 0 hearts -> Practice Mode: redo wrong questions, 5 correct = +1 heart, then resume the lesson
- Correct answer +10 XP, finish lesson +20 XP, Level = XP // 100 + 1
- Leaderboard: XP -> day streak -> who reached that XP first
- Daily quests and achievement badges
