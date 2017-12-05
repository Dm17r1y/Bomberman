#!/usr/bin/python3

from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import logic
import os
from level_creator import LevelCreator
from child_classes import *

RANDOM_LEVEL_SIZE = 15
TIMER_DELAY_MILLISECONDS = 30
BOMBERMAN_LIVES = 3


class GameController(GameController):
    pass


class PlayerController(PlayerController):

    def __init__(self):
        self._key = None

    def select_action(self):
        bomb = self._player.get_bomb()
        actions = {
            QtCore.Qt.Key_W: logic.Move(Direction.Down),
            QtCore.Qt.Key_S: logic.Move(Direction.Up),
            QtCore.Qt.Key_A: logic.Move(Direction.Left),
            QtCore.Qt.Key_D: logic.Move(Direction.Right),
            QtCore.Qt.Key_E: logic.PutBomb(bomb)
        }
        if self._key and self._key in actions:
            return actions[self._key]
        return logic.Move(Direction.Stand)

    def set_key(self, key):
        self._key = key

    def release_key(self):
        self._key = None


class BombermanWindow(QtWidgets.QWidget):

    def __init__(self, levels):
        super().__init__()
        self.levels = levels
        self.level_number = 0
        self.bomberman_lives = 3
        level = levels[0]
        width, height = self.initialize_game(level)
        self.view = BombermanView(self, width * CELL_SIZE, height * CELL_SIZE)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.make_turn)
        self.timer.start(TIMER_DELAY_MILLISECONDS)
        self.show()

    def closeEvent(self, event):
        self.timer = None

    def make_turn(self):
        animations = self.game.make_turn()
        self.view.set_animations(animations)
        self.view.repaint()

        if self.is_player_lose():
            self.get_lose_window()
        if self.is_player_win():
            self.get_win_window()

    def is_player_win(self):
        return self.game.monster_count == 0

    def is_player_lose(self):
        return self.game.player.is_dead

    def get_win_window(self):
        self.level_number += 1
        if self.level_number >= len(self.levels):
            reply = QtWidgets.QMessageBox.question(self, 'You win',
                                                   'You passed all levels',
                                                   QtWidgets.QMessageBox.Ok)
            self.timer.stop()
            self.close()
        else:
            reply = QtWidgets.QMessageBox.question(self,
                                                   'You win', 'Continue?',
                                                   QtWidgets.QMessageBox.Yes |
                                                   QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                level = self.levels[self.level_number]
                self.initialize_game(level)
            else:
                self.timer.stop()
                self.close()

    def get_lose_window(self):
        self.bomberman_lives -= 1
        reply = QtWidgets.QMessageBox.question(self, 'You lose',
                                               'You have {} lives. Continue?'
                                               .format(self.bomberman_lives),
                                               QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            if self.bomberman_lives <= 0:
                self.bomberman_lives = BOMBERMAN_LIVES
                self.level_number = 0
            self.initialize_game(self.levels[self.level_number])
        else:
            self.timer.stop()
            self.close()

    def initialize_game(self, level):

        legend = {
            "#": lambda: (UnbreakableBlock(),),
            "H": lambda: (DestroyableBlock(),),
            "@": lambda: (SimpleMonster(),),
            "h": lambda: (LongExplosionBonus(), DestroyableBlock()),
            "I": lambda: (ImmuneBonus(), DestroyableBlock()),
            "C": lambda: (CleverMonster(),),
            "E": lambda: (HighBombBonus(), DestroyableBlock()),
            "S": lambda: (StrongMonster(),),
            "F": lambda: (FortifiedBlock(),)
        }

        if level == "Random":
            game_map = LevelCreator.create_random_level(RANDOM_LEVEL_SIZE,
                                                        RANDOM_LEVEL_SIZE)
            level_width = RANDOM_LEVEL_SIZE
            level_height = RANDOM_LEVEL_SIZE
        else:
            level_creator = LevelCreator(legend)
            with open(level) as f:
                level_ = f.read().split('\n')
            game_map, level_width, level_height = \
                level_creator.create_level(level_)
        self.controller = PlayerController()
        player = Player(self.controller)
        player.set_bomb_type(SimpleBomb)
        game_map.add_map_object(player, Point(CELL_SIZE, CELL_SIZE))
        self.game = Game(game_map, GameController(), player)
        return level_width, level_height

    def keyPressEvent(self, key_event):
        self.controller.set_key(key_event.key())

    def keyReleaseEvent(self, key_event):
        self.controller.release_key()


class BombermanView(QtWidgets.QFrame):

    def __init__(self, window, width, height):
        QtWidgets.QFrame.__init__(self, window)
        self.width_ = width
        self.height_ = height
        self.resize(width, height)
        self.setStyleSheet("background-color: cyan")
        self.animations = []
        self.load_images()

    def load_images(self):

        class Image:
            def __init__(self, path_to_image):
                self._image = QtGui.QPixmap(path_to_image) \
                    .scaled(CELL_SIZE, CELL_SIZE)

            @property
            def image(self):
                return self._image

        unbreakable_block_image = Image("images/unbreakable_block.png")
        destroyable_block_image = Image("images/destroyable_block.png")
        fortified_block_image = Image("images/fortified_block.png")
        player_image = Image("images/player.png")
        bomb_image = Image("images/bomb.png")
        explosion_central_image = Image("images/explosion_center.png")
        explosion_right_image = Image("images/explosion_right.png")
        explosion_left_image = Image("images/explosion_left.png")
        explosion_up_image = Image("images/explosion_up.png")
        explosion_down_image = Image("images/explosion_down.png")
        explosion_vertical_image = Image("images/explosion_vertical.png")
        explosion_horizontal_image = Image("images/explosion_horizontal.png")
        simple_monster_image = Image("images/simple_monster.png")
        clever_monster_image = Image("images/clever_monster.png")
        strong_monster_image = Image("images/strong_monster.png")
        high_bomb_bonus_image = Image("images/high_bomb_bonus.png")
        immune_bonus_image = Image("images/immune_bonus.png")
        long_explosion_bonus_image = Image("images/long_explosion_bonus.png")

        self.images = {
            UnbreakableBlock: unbreakable_block_image,
            Player: player_image,
            SimpleBomb: bomb_image,
            HighPowerBomb: bomb_image,
            SimpleMonster: simple_monster_image,
            CleverMonster: clever_monster_image,
            StrongMonster: strong_monster_image,
            HighBombBonus: high_bomb_bonus_image,
            ImmuneBonus: immune_bonus_image,
            LongExplosionBonus: long_explosion_bonus_image,
            DestroyableBlock: destroyable_block_image,
            FortifiedBlock: fortified_block_image
        }

        self.explosion_images = {
            Direction.Up: explosion_down_image,
            Direction.Down: explosion_up_image,
            Direction.Left: explosion_left_image,
            Direction.Right: explosion_right_image
        }
        self.explosion_vertical_image = explosion_vertical_image
        self.explosion_horizontal_image = explosion_horizontal_image
        self.explosion_central_image = explosion_central_image

    def set_animations(self, animations):
        priority = {
            Player: 0,
            SimpleMonster: 1,
            StrongMonster: 1,
            CleverMonster: 1,
            Block: 1,
            UnbreakableBlock: 1,
            FortifiedBlock: 1,
            SimpleBomb: 1,
            HighPowerBomb: 1,
            ExplosionBlock: 2,
            HighPoweredExplosion: 2,
            DestroyableBlock: 3,
            Bonus: 4,
            ImmuneBonus: 4,
            ImmuneBuff: 4,
            LongRangeExplosionBuff: 4,
            LongExplosionBonus: 4,
            HighBombBonus: 4
        }
        self.animations = animations
        self.animations.sort(key=lambda animation:priority[
            type(animation.object)
        ], reverse=True)

    def paintEvent(self, paint_event):
        painter = QtGui.QPainter(self)
        self.draw_background(painter)
        self.draw_game_objects(painter)

    def draw_background(self, painter):
        background_rect = QtCore.QRect(0, 0, self.width_ * CELL_SIZE,
                                       self.height_ * CELL_SIZE)
        painter.fillRect(background_rect, QtCore.Qt.cyan)

    def draw_game_objects(self, painter):

        for animation in self.animations:
            image = self.get_image(animation, self.animations)
            location = animation.location + animation.direction.value
            point = QtCore.QPoint(location.x, location.y)
            painter.drawPixmap(point, image.image)

    def get_image(self, animation, animations):

        opposite = {
            Direction.Left: Direction.Right,
            Direction.Right: Direction.Left,
            Direction.Up: Direction.Down,
            Direction.Down: Direction.Up
        }

        if isinstance(animation.object, logic.ExplosionBlock):
            animation_points = {anim.location for anim in animations
                                if isinstance(anim.object,
                                              logic.ExplosionBlock)}
            neighboring_explosions = []
            for direction in (Direction.Left, Direction.Right,
                              Direction.Up, Direction.Down):
                if animation.location + (direction.value * CELL_SIZE)\
                        in animation_points:
                    neighboring_explosions.append(direction)

            if len(neighboring_explosions) == 1:
                return self.explosion_images[
                    opposite[neighboring_explosions[0]]
                ]
            elif len(neighboring_explosions) == 2:
                if set(neighboring_explosions) == \
                        {Direction.Up, Direction.Down}:
                    return self.explosion_vertical_image
                elif set(neighboring_explosions) == \
                        {Direction.Left, Direction.Right}:
                    return self.explosion_horizontal_image
            return self.explosion_central_image
        else:
            return self.images[type(animation.object)]


class MainWindow(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        start_button = QtWidgets.QPushButton("Start")
        start_button.clicked.connect(self.start)
        layout.addWidget(start_button)

        directories = os.listdir('levels') + ["Random"]
        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.addItems(directories)
        layout.addWidget(self.combo_box)
        self.setLayout(layout)
        self.show()

    def start(self):
        level = self.combo_box.currentText()
        if level == "Random":
            self.window = BombermanWindow(["Random"])
        else:
            levels = os.listdir(os.path.join('levels', level))
            levels = [os.path.join('levels', level, name) for name in levels]
            self.window = BombermanWindow(levels)


def main():
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
