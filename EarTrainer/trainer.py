"""Генератор вопросов + проверка ответов."""
import random
import theory
import synth


class IntervalQuestion:
    def __init__(self, level: int = 1, direction: str = "up"):
        pool = theory.intervals_for_level(level)
        self.semitones, self.short, self.ru, self.diff = random.choice(pool)
        self.direction = direction
        self.root = random.randint(60, 72)

    def play(self):
        synth.play_interval(self.root, self.semitones, self.direction)

    @property
    def answer_ru(self) -> str:
        return self.ru

    def check(self, semitones: int) -> bool:
        return semitones == self.semitones

    def choices(self, level: int = 1):
        pool = theory.intervals_for_level(level)
        others = [i for i in pool if i[0] != self.semitones]
        random.shuffle(others)
        wrong = others[:3]
        correct = next(i for i in pool if i[0] == self.semitones)
        opts = wrong + [correct]
        random.shuffle(opts)
        return opts


class ChordQuestion:
    def __init__(self, level: int = 1):
        pool = theory.chords_for_level(level)
        self.key, self.semis, self.ru, self.diff = random.choice(pool)
        self.root = random.randint(55, 67)

    def play(self):
        synth.play_chord(self.root, self.semis)

    @property
    def answer_ru(self) -> str:
        return self.ru

    def check(self, key: str) -> bool:
        return key == self.key

    def choices(self, level: int = 1):
        pool = theory.chords_for_level(level)
        others = [c for c in pool if c[0] != self.key]
        random.shuffle(others)
        wrong = others[:3]
        correct = next(c for c in pool if c[0] == self.key)
        opts = wrong + [correct]
        random.shuffle(opts)
        return opts


class NoteQuestion:
    def __init__(self, level: int = 1):
        pool = theory.note_pool(level)
        self.pitch_class = random.choice(pool)
        self.octave = 4
        self.note = 12 * (self.octave + 1) + self.pitch_class

    def play(self):
        synth.play_note(self.note, duration=1.2)

    @property
    def answer_ru(self) -> str:
        return theory.NOTE_NAMES_RU[self.pitch_class]

    def check(self, pitch_class: int) -> bool:
        return pitch_class == self.pitch_class

    def choices(self, level: int = 1):
        pool = theory.note_pool(level)
        others = [p for p in pool if p != self.pitch_class]
        random.shuffle(others)
        wrong = others[:3]
        correct = self.pitch_class
        opts = wrong + [correct]
        random.shuffle(opts)
        return opts


class Session:
    def __init__(self, mode: str, level: int = 1, direction: str = "up"):
        self.mode = mode
        self.level = level
        self.direction = direction
        self.correct = 0
        self.wrong = 0
        self.streak = 0
        self.best_streak = 0
        self.total = 0
        self.current = None
        self._next()

    def _next(self):
        if self.mode == "interval":
            self.current = IntervalQuestion(self.level, self.direction)
        elif self.mode == "chord":
            self.current = ChordQuestion(self.level)
        elif self.mode == "note":
            self.current = NoteQuestion(self.level)

    def submit(self, answer) -> bool:
        ok = self.current.check(answer)
        self.total += 1
        if ok:
            self.correct += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            synth.play_success()
        else:
            self.wrong += 1
            self.streak = 0
            synth.play_fail()
        return ok

    def next_question(self):
        self._next()

    @property
    def accuracy(self) -> float:
        return (self.correct / self.total * 100) if self.total else 0.0
