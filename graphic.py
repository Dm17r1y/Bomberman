#!/usr/bin/python3

from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import logic
import os
from level_creator import LevelCreator
from child_classes import *
import copy
from PyQt5.QtCore import Qt
from controller import *

RANDOM_LEVEL_SIZE = 15
TIMER_DELAY_MILLISECONDS = 30
BOMBERMAN_LIVES = 3

cell_size_in_pixels = 16


class Cheat:

    def __init__(self, sequence, effect):
        self._sequence = sequence
        self._effect = effect
        self._progress = 0

    def register_key(self, key):
        if key == self._sequence[self._progress]:
            self._progress += 1
            if self._progress == len(self._sequence):
                self._progress = 0
                self._effect()
        else:
            self._progress = 0


class GameController(GameController):

    def __init__(self, window, cheats):
        self._save = None
        self._window = window
        self._cheats = cheats

    @property
    def save(self):
        return copy.deepcopy(self._save)

    def delete_save(self):
        self._save = None

    def handle_key(self, key):

        class Save:

            def __init__(self, game):
                self.game = copy.deepcopy(game)

        if key == QtCore.Qt.Key_F5 and self._save is None:
            game = self._window.game
            self._save = Save(game)

        for cheat in self._cheats:
            cheat.register_key(key)


class PlayerController(PlayerController):

    def __init__(self):
        self._key = None
        self._active_keys = [Qt.Key_W, Qt.Key_S, Qt.Key_A, Qt.Key_D,
                             Qt.Key_Space]

    def select_action(self):
        actions = {
            self._active_keys[0]: logic.Move(Direction.Down),
            self._active_keys[1]: logic.Move(Direction.Up),
            self._active_keys[2]: logic.Move(Direction.Left),
            self._active_keys[3]: logic.Move(Direction.Right),
            self._active_keys[4]: logic.PutBomb(self._player.get_bomb())
        }
        if self._key and self._key in actions:
            return actions[self._key]
        return logic.Move(Direction.Stand)

    def set_active_keys(self, new_keys):
        if len(new_keys) != 5:
            raise Exception("len of new keys must be 5 but was {}"
                            .format(len(new_keys)))
        self._active_keys = new_keys

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
        width, height = self.initialize_new_game(level)
        self.view = BombermanView(self, width * cell_size_in_pixels,
                                  height * cell_size_in_pixels)
        cheats = self.generate_cheats()
        self.game_controller = GameController(self, cheats)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.make_turn)
        self.timer.start(TIMER_DELAY_MILLISECONDS)
        self.show()

    def generate_cheats(self):

        cheats = []

        def add_immune_buff():
            self.game.player.add_buff(ImmuneBuff())

        def add_long_explon_buff():
            self.game.player.add_buff(LongRangeExplosionBuff())

        def add_high_explosion_buff():
            self.game.player.set_bomb_type(HighPowerBomb)

        def win_level():
            self.win_flag = True

        def change_buttons_like_vim():
            new_keys = [Qt.Key_K, Qt.Key_J, Qt.Key_H, Qt.Key_L, Qt.Key_Space]
            self.player_controller.set_active_keys(new_keys)

        def add_walking_to_the_wall():
            self.game.player.set_ghost_mode(True)

        cheats.append(Cheat([Qt.Key_I, Qt.Key_M, Qt.Key_M, Qt.Key_U,
                             Qt.Key_N, Qt.Key_E], add_immune_buff))
        cheats.append(Cheat([Qt.Key_L, Qt.Key_O, Qt.Key_N, Qt.Key_G,
                             Qt.Key_E, Qt.Key_X, Qt.Key_P, Qt.Key_L,
                             Qt.Key_O, Qt.Key_S, Qt.Key_I, Qt.Key_O,
                             Qt.Key_N], add_long_explon_buff))
        cheats.append(Cheat([Qt.Key_H, Qt.Key_I, Qt.Key_G, Qt.Key_H,
                             Qt.Key_E, Qt.Key_X, Qt.Key_P, Qt.Key_L,
                             Qt.Key_O, Qt.Key_S, Qt.Key_I, Qt.Key_O,
                             Qt.Key_N], add_high_explosion_buff))
        cheats.append(Cheat([Qt.Key_W, Qt.Key_I, Qt.Key_N, Qt.Key_L,
                             Qt.Key_E, Qt.Key_V, Qt.Key_E, Qt.Key_L],
                            win_level))
        cheats.append(Cheat([Qt.Key_V, Qt.Key_I, Qt.Key_M, Qt.Key_H,
                             Qt.Key_J, Qt.Key_K, Qt.Key_L],
                            change_buttons_like_vim))
        cheats.append(Cheat([Qt.Key_G, Qt.Key_H, Qt.Key_O, Qt.Key_S,
                             Qt.Key_T, Qt.Key_M, Qt.Key_O, Qt.Key_D,
                             Qt.Key_E], add_walking_to_the_wall))
        return cheats

    def closeEvent(self, event):
        self.timer = None

    def make_turn(self):
        animations = self.game.make_turn()
        self.view.set_animations(animations)
        self.view.repaint()

        if self.is_player_lose():
            self.get_lose_window()
        if self.is_player_win() or self.win_flag:
            self.get_win_window()

    def is_player_win(self):
        return self.game.monster_count == 0

    def is_player_lose(self):
        return self.game.player.is_dead

    def get_win_window(self):
        self.level_number += 1
        self.game_controller.delete_save()
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
                self.initialize_new_game(level)
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
                self.game_controller.delete_save()
                self.initialize_new_game(self.levels[0])
            elif self.game_controller.save is not None:
                self.game = self.game_controller.save.game
                self.game.player.set_controller(self.player_controller)
            else:
                self.initialize_new_game(self.levels[self.level_number])

        else:
            self.timer.stop()
            self.close()

    def initialize_new_game(self, level):

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

        self.win_flag = False

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
        self.player_controller = PlayerController()
        player = Player(self.player_controller)
        player.set_bomb_type(SimpleBomb)
        game_map.add_map_object(player, Point(CELL_SIZE, CELL_SIZE))
        self.game = Game(game_map, player)
        return level_width, level_height

    def keyPressEvent(self, key_event):
        self.game_controller.handle_key(key_event.key())
        self.player_controller.set_key(key_event.key())

    def keyReleaseEvent(self, key_event):
        self.player_controller.release_key()


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
                    .scaled(cell_size_in_pixels, cell_size_in_pixels)

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

        def get_priority(animation):
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
            if isinstance(animation.object, ExplosionBlock):
                return 1.5 if animation.object.direction == Direction.Stand \
                           else 2
            return priority[type(animation.object)]

        self.animations = animations
        self.animations.sort(key=get_priority ,reverse=True)

    def paintEvent(self, paint_event):
        painter = QtGui.QPainter(self)
        self.draw_background(painter)
        self.draw_game_objects(painter)

    def draw_background(self, painter):
        background_rect = QtCore.QRect(0, 0, self.width_ * cell_size_in_pixels,
                                       self.height_ * cell_size_in_pixels)
        painter.fillRect(background_rect, QtCore.Qt.cyan)

    def draw_game_objects(self, painter):

        for animation in self.animations:
            image = self.get_image(animation, self.animations)
            location = animation.location + animation.direction.value
            point = QtCore.QPoint(
                location.x * (cell_size_in_pixels / CELL_SIZE),
                location.y * (cell_size_in_pixels / CELL_SIZE)
            )
            painter.drawPixmap(point, image.image)

    def get_image(self, animation, animations):

        opposite = {
            Direction.Left: Direction.Right,
            Direction.Right: Direction.Left,
            Direction.Up: Direction.Down,
            Direction.Down: Direction.Up
        }

        if isinstance(animation.object, logic.ExplosionBlock):
            return self.get_explosion_image(animation.object,
                                            animation.location, animations)
        else:
            return self.images[type(animation.object)]

    def get_explosion_image(self, explosion, coordinates, animations):
        if explosion.direction == Direction.Stand:
            return self.explosion_central_image
        elif coordinates + explosion.direction.value * CELL_SIZE in animations:
            images = {
                Direction.Right: self.explosion_horizontal_image,
                Direction.Left: self.explosion_horizontal_image,
                Direction.Up: self.explosion_vertical_image,
                Direction.Down: self.explosion_vertical_image
            }
            return images[explosion.direction]
        else:
            return self.explosion_images[explosion.direction]

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
            levels.sort()
            self.window = BombermanWindow(levels)


def main():
    global cell_size_in_pixels
    app = QtWidgets.QApplication(sys.argv)
    resolution =  app.desktop().width() * app.desktop().height()
    if resolution >= 1920 * 1080:
        cell_size_in_pixels = 32
    main_window = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
