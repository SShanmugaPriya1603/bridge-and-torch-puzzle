import tkinter as tk
from tkinter import messagebox, simpledialog
import time
import heapq
from itertools import combinations

class BridgeTorchPuzzle:
    def __init__(self, root):
        self.root = root
        self.root.title("Bridge and Torch Puzzle")
        self.root.geometry("800x600")
        self.root.configure(bg="#e0f7fa")
        self.high_scores = {"Easy": float('inf'), "Medium": float('inf'), "Hard": float('inf')}
        self.show_title_and_rules()

    def show_title_and_rules(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        title_frame = tk.Frame(self.root, bg="#0288d1", pady=20)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="Bridge and Torch Puzzle", font=("Arial", 30, "bold"), fg="white", bg="#0288d1").pack()

        rules_frame = tk.Frame(self.root, bg="#e0f7fa", pady=20)
        rules_frame.pack(pady=20)
        rules_text = (
            "Rules:\n"
            "- People must cross a bridge with a torch.\n"
            "- Up to 2 can cross, torch required.\n"
            "- Time is the slower person's.\n"
            "- Goal: Minimize total time!\n"
            "- Click to select (red = selected)."
        )
        tk.Label(rules_frame, text=rules_text, font=("Arial", 14), justify="left", bg="#e0f7fa").pack()

        scores_frame = tk.Frame(self.root, bg="#e0f7fa")
        scores_frame.pack(pady=10)
        tk.Label(scores_frame, text="High Scores", font=("Arial", 14, "bold"), bg="#e0f7fa").pack()
        for level, score in self.high_scores.items():
            tk.Label(scores_frame, text=f"{level}: {score if score != float('inf') else 'N/A'} mins", font=("Arial", 12), bg="#e0f7fa").pack()

        btn_frame = tk.Frame(self.root, bg="#e0f7fa")
        btn_frame.pack(pady=20)
        for text, cmd in [("Easy", lambda: self.setup_game("Easy")),
                          ("Medium", lambda: self.setup_game("Medium")),
                          ("Hard", lambda: self.setup_game("Hard"))]:
            btn = tk.Button(btn_frame, text=text, font=("Arial", 12), bg="#4fc3f7", fg="white", relief="flat", command=cmd)
            btn.pack(side=tk.LEFT, padx=10, pady=5)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#81d4fa"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#4fc3f7"))

    def setup_game(self, difficulty):
        difficulty_settings = {
            "Easy": {0: 1, 1: 2, 2: 3},
            "Medium": {0: 1, 1: 2, 2: 5, 3: 10},
            "Hard": {0: 2, 1: 3, 2: 10, 3: 15}
        }
        self.people_times = difficulty_settings[difficulty]
        optimal_times = {"Easy": 6, "Medium": 17, "Hard": 30}
        self.start_game(difficulty, optimal_times[difficulty])

    def start_game(self, difficulty, optimal_time):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.difficulty = difficulty
        self.optimal_time = optimal_time
        self.left_bank = set(self.people_times.keys())
        self.right_bank = set()
        self.total_time = 0
        self.time_limit = optimal_time
        self.torch_on_left = True
        self.positions = {}
        self.torch_id = None
        self.selected_people = []
        self.moves = []
        self.is_animating = False

        self.canvas = tk.Canvas(self.root, width=800, height=400, bg="#b3e5fc")
        self.canvas.pack(pady=20)
        self.draw_background()

        self.time_label = tk.Label(self.root, text=f"Time: {self.total_time}/{self.time_limit} mins", font=("Arial", 14, "bold"), bg="#e0f7fa")
        self.time_label.pack(pady=5)
        self.moves_text = tk.Text(self.root, height=5, width=50, font=("Arial", 12), bg="#ffffff", relief="sunken")
        self.moves_text.pack(pady=10)

        btn_frame = tk.Frame(self.root, bg="#e0f7fa")
        btn_frame.pack(pady=10)
        for text, cmd in [("Cross Bridge", self.cross_bridge), ("Return", self.return_torch), ("Reset", self.reset), ("Show Solution", self.show_solution)]:
            btn = tk.Button(btn_frame, text=text, font=("Arial", 12), bg="#4fc3f7", fg="white", relief="flat", command=cmd)
            btn.pack(side=tk.LEFT, padx=10)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#81d4fa"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#4fc3f7"))

        self.canvas.bind("<Button-1>", self.select_person)
        self.update_display()
        self.update_timer()

    def draw_background(self):
        self.canvas.create_rectangle(0, 200, 800, 400, fill="#4caf50", outline="")
        self.canvas.create_rectangle(300, 200, 500, 400, fill="#0288d1", outline="")
        self.canvas.create_rectangle(300, 250, 500, 300, fill="#8d5524", outline="black", width=2)
        self.canvas.create_text(150, 30, text="Left Bank", font=("Arial", 14, "bold"), fill="white")
        self.canvas.create_text(650, 30, text="Right Bank", font=("Arial", 14, "bold"), fill="white")

    def draw_person(self, person_id, x, y, selected=False):
        colors = ["#ff8a65", "#ab47bc", "#4dd0e1", "#ffd54f"]
        head = self.canvas.create_oval(x-15, y-30, x+15, y, fill="#ffe0b2", outline="black")
        body = self.canvas.create_rectangle(x-10, y, x+10, y+40, fill=colors[person_id % 4] if not selected else "#f44336", outline="black")
        label = self.canvas.create_text(x, y-40, text=f"P{person_id} ({self.people_times[person_id]}m)", font=("Arial", 10, "bold"), fill="white")
        return [head, body, label]

    def draw_torch(self, x, y):
        return self.canvas.create_polygon(x+15, y+20, x+25, y+20, x+20, y+10, fill="#ffca28", outline="black")

    def update_display(self):
        for items in self.positions.values():
            for item in items:
                self.canvas.delete(item)
        if self.torch_id:
            self.canvas.delete(self.torch_id)
        self.positions.clear()

        left_spacing = min(80, 250 // max(1, len(self.left_bank)))
        for i, person in enumerate(sorted(self.left_bank)):
            x = 50 + i * left_spacing
            y = 250
            selected = person in self.selected_people
            self.positions[person] = self.draw_person(person, x, y, selected)
            if self.torch_on_left and person == min(self.left_bank, default=None):
                self.torch_id = self.draw_torch(x, y)

        right_spacing = min(80, 250 // max(1, len(self.right_bank)))
        for i, person in enumerate(sorted(self.right_bank)):
            x = 550 + i * right_spacing
            y = 250
            selected = person in self.selected_people
            self.positions[person] = self.draw_person(person, x, y, selected)
            if not self.torch_on_left and person == min(self.right_bank, default=None):
                self.torch_id = self.draw_torch(x, y)

        self.time_label.config(text=f"Time: {self.total_time}/{self.time_limit} mins", fg="red" if self.total_time > self.time_limit else "black")

    def select_person(self, event):
        if self.is_animating:
            return
        x, y = event.x, event.y
        for person, items in list(self.positions.items()):
            head = items[0]
            coords = self.canvas.coords(head)
            if coords[0] <= x <= coords[2] and coords[1] <= y <= coords[3]:
                if (self.torch_on_left and person in self.left_bank) or (not self.torch_on_left and person in self.right_bank):
                    if person in self.selected_people:
                        self.selected_people.remove(person)
                    elif len(self.selected_people) < 2:
                        self.selected_people.append(person)
                    self.update_display()
                break

    def animate_crossing(self, person_ids, to_right=True):
        self.is_animating = True
        start_x = 50 if to_right else 550
        end_x = 550 if to_right else 50
        for person in person_ids:
            items = self.positions[person]
            dx = (end_x - start_x) / 50
            for _ in range(50):
                for item in items:
                    self.canvas.move(item, dx, 0)
                if person == person_ids[-1]:
                    self.canvas.move(self.torch_id, dx, 0)
                self.root.update()
                time.sleep(0.02)
        self.is_animating = False
        self.update_display()

    def cross_bridge(self):
        if self.is_animating or not self.torch_on_left or len(self.selected_people) == 0 or len(self.selected_people) > 2:
            messagebox.showerror("Error", "Select 1 or 2 people on the left bank with the torch!")
            return

        cost = max(self.people_times[p] for p in self.selected_people)
        self.total_time += cost
        for person in self.selected_people:
            self.left_bank.remove(person)
            self.right_bank.add(person)
        self.torch_on_left = False
        self.moves.append(f"Persons {self.selected_people} cross ({cost} mins)")
        self.moves_text.insert(tk.END, f"Persons {self.selected_people} cross ({cost} mins)\n")
        self.animate_crossing(self.selected_people, to_right=True)
        self.selected_people.clear()
        self.check_game_over()

    def return_torch(self):
        if self.is_animating or self.torch_on_left or len(self.selected_people) != 1:
            messagebox.showerror("Error", "Select 1 person on the right bank with the torch!")
            return

        person = self.selected_people[0]
        cost = self.people_times[person]
        self.total_time += cost
        self.right_bank.remove(person)
        self.left_bank.add(person)
        self.torch_on_left = True
        self.moves.append(f"Person {person} returns ({cost} mins)")
        self.moves_text.insert(tk.END, f"Person {person} returns ({cost} mins)\n")
        self.animate_crossing([person], to_right=False)
        self.selected_people.clear()

    def check_game_over(self):
        if not self.left_bank:
            result = "You Win!" if self.total_time <= self.optimal_time else "You Lose!"
            if self.difficulty != "Custom" and self.total_time < self.high_scores[self.difficulty]:
                self.high_scores[self.difficulty] = self.total_time
            messagebox.showinfo("Game Over", f"{result} Completed in {self.total_time} mins. Optimal is {self.optimal_time} mins.")
            self.show_title_and_rules()

    def reset(self):
        if self.is_animating:
            return
        self.left_bank = set(self.people_times.keys())
        self.right_bank = set()
        self.total_time = 0
        self.torch_on_left = True
        self.selected_people.clear()
        self.moves = []
        self.moves_text.delete(1.0, tk.END)
        self.update_display()

    def solve_puzzle(self):
        # State: (frozenset(left_bank), frozenset(right_bank), torch_on_left, total_time)
        start_state = (frozenset(self.people_times.keys()), frozenset(), True, 0)
        goal_state = frozenset()

        def heuristic(left_bank, right_bank, torch_on_left):
            if not left_bank:
                return 0
            times = sorted([self.people_times[p] for p in left_bank], reverse=True)
            if len(times) <= 2:
                return max(times) if times else 0
            trips = (len(left_bank) + 1) // 2  # Number of crossings needed
            returns = max(0, trips - 1)  # Number of returns
            return max(times[0], sum(times[:2]) + min(self.people_times.values()) * returns)

        open_set = [(heuristic(*start_state[:3]), 0, start_state)]  # f_score, g_score, state
        heapq.heapify(open_set)
        g_score = {start_state: 0}
        f_score = {start_state: heuristic(*start_state[:3])}
        came_from = {}

        while open_set:
            f, g, current = heapq.heappop(open_set)
            left_bank, right_bank, torch_on_left, total_time = current

            if left_bank == goal_state:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_state)
                path.reverse()
                moves = []
                for i in range(1, len(path)):
                    prev = path[i-1]
                    curr = path[i]
                    if prev[2]:  # torch was on left
                        crossers = tuple(prev[0] - curr[0])
                        moves.append((crossers, True))
                    else:
                        crossers = tuple(curr[0] - prev[0])
                        moves.append((crossers, False))
                # Debug output
                total = 0
                for crossers, to_right in moves:
                    cost = max(self.people_times[p] for p in crossers)
                    total += cost
                    print(f"{'Cross' if to_right else 'Return'}: {crossers}, Cost: {cost}, Total: {total}")
                return moves

            if torch_on_left:
                from_bank, to_bank = left_bank, right_bank
                for r in range(1, min(3, len(from_bank) + 1)):
                    for crossers in combinations(from_bank, r):
                        new_left = left_bank - set(crossers)
                        new_right = right_bank | set(crossers)
                        cost = max(self.people_times[p] for p in crossers)
                        new_state = (frozenset(new_left), frozenset(new_right), False, total_time + cost)
                        tentative_g = g_score[current] + cost
                        if new_state not in g_score or tentative_g < g_score[new_state]:
                            g_score[new_state] = tentative_g
                            f_score[new_state] = tentative_g + heuristic(new_left, new_right, False)
                            came_from[new_state] = current
                            heapq.heappush(open_set, (f_score[new_state], tentative_g, new_state))
            else:
                from_bank, to_bank = right_bank, left_bank
                for person in from_bank:
                    crossers = (person,)
                    new_left = left_bank | set(crossers)
                    new_right = right_bank - set(crossers)
                    cost = self.people_times[person]
                    new_state = (frozenset(new_left), frozenset(new_right), True, total_time + cost)
                    tentative_g = g_score[current] + cost
                    if new_state not in g_score or tentative_g < g_score[new_state]:
                        g_score[new_state] = tentative_g
                        f_score[new_state] = tentative_g + heuristic(new_left, new_right, True)
                        came_from[new_state] = current
                        heapq.heappush(open_set, (f_score[new_state], tentative_g, new_state))

        return None

    def show_solution(self):
        if self.is_animating:
            return
        self.reset()
        solution = self.solve_puzzle()
        if not solution:
            messagebox.showinfo("Solution", "No solution found!")
            return

        for crossers, to_right in solution:
            self.selected_people = list(crossers)
            if to_right:
                self.cross_bridge()
            else:
                self.return_torch()
            time.sleep(1.5)
            self.root.update()

    def update_timer(self):
        self.time_label.config(text=f"Time: {self.total_time}/{self.time_limit} mins", fg="red" if self.total_time > self.time_limit else "black")
        if self.left_bank:
            self.root.after(1000, self.update_timer)

def main():
    root = tk.Tk()
    app = BridgeTorchPuzzle(root)
    root.mainloop()

if __name__ == "__main__":
    main()