import tkinter as tk
import random
from tkinter import messagebox  # Import untuk dialog konfirmasi


class GameObject:
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 10
        self.direction = [1, -1]
        self.speed = 5  # Kecepatan bola
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='white', outline='blue')
        super().__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 100
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#abc4ff', outline='#000000')
        super().__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super().move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#ED639E', 2: '#8FE1A2', 3: '#FFFF00'}
    
    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super().__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
            self.canvas.master.score += 10  # Menambah skor
            self.canvas.master.update_score()
        else:
            self.canvas.itemconfig(self.item,
                                   fill=Brick.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.lives = 3
        self.score = 0
        self.level = 1
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#1F1B61',
                                width=self.width,
                                height=self.height)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 350)
        self.items[self.paddle.item] = self.paddle
        self.hud = None
        self.is_paused = False  
        self.setup_game()

        self.canvas.focus_set()
        self.canvas.bind('<Left>', lambda _: self.paddle.move(-15))
        self.canvas.bind('<Right>', lambda _: self.paddle.move(15))

        self.pause_button = tk.Button(self, text="Pause", command=self.toggle_pause)
        self.pause_button.pack()

    def setup_game(self):
        self.add_ball()
        self.update_hud()
        self.add_bricks()
        self.text = self.draw_text(300, 200, 'Press Space to Start')
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 330)
        self.paddle.set_ball(self.ball)

    def add_bricks(self):
        """Menambahkan balok sesuai dengan level"""
        brick_rows = self.level  # Jumlah baris balok berdasarkan level
        for i in range(brick_rows):
            y_position = 50 + (i * 30)  # Setiap baris balok naik 30px
            for x in range(5, self.width - 5, 75):  # Setiap balok dengan jarak 75px
                color = random.choice([1, 2, 3])  # Setiap balok memiliki warna acak
                self.add_brick(x + 37.5, y_position, color)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40'):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text, font=font, fill='white')

    def update_hud(self):
        hud_text = f"Lives: {self.lives}   Score: {self.score}   Level: {self.level}"
        if self.hud is None:
            self.hud = self.draw_text(300, 20, hud_text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=hud_text)

    def update_score(self):
        self.update_hud()

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        if not self.is_paused:
            self.check_collisions()
            num_bricks = len(self.canvas.find_withtag('brick'))
            if num_bricks == 0:
                if self.level == 3:
                    self.display_winner()  # Menampilkan kemenangan hanya pada level 3
                else:
                    self.level += 1  # Lanjutkan ke level berikutnya
                    self.setup_game()
            elif self.ball.get_position()[3] >= self.height:
                self.lives -= 1
                if self.lives < 0:
                    self.draw_text(300, 200, f"Game Over! Final Score: {self.score}")
                else:
                    self.after(1000, self.setup_game)
            else:
                self.ball.update()
                self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)

    def display_winner(self):
        # Menampilkan efek kemenangan setelah level 3 selesai
        text = self.draw_text(300, 200, "You Win!", size='50')
        self.animate_winner(text)
        self.after(2000, self.quit_game)  # Keluar permainan setelah 2 detik

    def animate_winner(self, text):
        def blink():
            current_color = self.canvas.itemcget(text, 'fill')
            next_color = 'yellow' if current_color == 'white' else 'white'
            self.canvas.itemconfig(text, fill=next_color)
            self.after(500, blink)

        blink()

    def quit_game(self):
        """Menutup game setelah 2 detik"""
        self.quit()

    def toggle_pause(self):
        """Fungsi untuk menjeda atau melanjutkan permainan."""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.config(text="Resume")  
        else:
            self.pause_button.config(text="Pause")  
            self.game_loop()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break the Bricks! - Victory Edition')
    game = Game(root)
    game.mainloop()
