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
ANIMATION_CONTINUATION_IN_TICKS = 4

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
                             Qt.Key_T], add_walking_to_the_wall))
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


class Image:
    def __init__(self, path_to_image):
        self._image = QtGui.QPixmap(path_to_image) \
            .scaled(cell_size_in_pixels, cell_size_in_pixels)

    @property
    def image(self):
        return self._image


class DrawAnimation:
    def __init__(self, image):
        self._image = image

    def get_animation_image(self, _, __):
        return self._image


class ActorDrawAnimation:
    def __init__(self, go_left_images, go_right_images, go_up_images,
                 go_down_images, stand_image, die_images):
        self._images = {
            Direction.Down: go_down_images,
            Direction.Up: go_up_images,
            Direction.Right: go_right_images,
            Direction.Left: go_left_images,
        }
        self.stand_image = stand_image
        self._die_images = die_images

    def get_animation_image(self, animation, animation_state):
        state = animation_state.state // ANIMATION_CONTINUATION_IN_TICKS
        if animation.direction == Direction.Stand:
            return self.stand_image
        return self._images[animation.direction][
            state % len(self._images[animation.direction])
        ]

    def get_dead_animation(self):
        return DeadAnimations(self._die_images)


class ExplosionDrawAnimation:
    def __init__(self, left_images, right_images, up_images, down_images,
                 central_images, vertical_images, horizontal_images):
        self._final_images = {
            Direction.Left: left_images,
            Direction.Right: right_images,
            Direction.Up: up_images,
            Direction.Down: down_images,
        }
        self._images = {
            Direction.Left: horizontal_images,
            Direction.Right: horizontal_images,
            Direction.Up: vertical_images,
            Direction.Down: vertical_images,
        }
        self._central_images = central_images

    def get_animation_image(self, animation, animation_state):
        state = animation_state.state
        is_final_animation = animation_state.is_final_animation
        direction = animation.object.direction
        if direction == Direction.Stand:
            return self._central_images[state % len(self._central_images)]
        elif is_final_animation:
            return self._final_images[direction][
                state % len(self._final_images[direction])
            ]
        else:
            return self._images[direction][state %
                                           len(self._images[direction])]


class DeadAnimations:
    def __init__(self, die_images):
        self._die_images = die_images

    def get_animation_image(self, animation_state):
        return self._die_images[animation_state.state % len(self._die_images)]


class StateSwitcher:

    class AnimationState:
        def __init__(self, state, previous_state, previous_direction,
                     is_final_animation=False):
            self.state = state
            self.previous_state = previous_state
            self.previous_direction = previous_direction
            self.is_final_animation = is_final_animation

    class State:
        def __init__(self):
            self.state = 0
            self.previous_state = 0
            self.previous_direction = Direction.Down

        def switch_state(self, animation):
            self.previous_state = self.state
            if animation.direction == self.previous_direction:
                self.state += 1
            else:
                self.state = 0
                self.previous_direction = animation.direction
            return StateSwitcher.AnimationState(
                self.state, self.previous_state, self.previous_direction
            )

    class ExplosionState:
        def __init__(self, state_count, is_final_animation):
            self.state_counts = state_count
            self.is_final_animation = is_final_animation

        def switch_state(self, animation):
            state = int(animation.object.life_time / EXPLOSION_LIVE *
                        self.state_counts)
            animation = StateSwitcher.AnimationState(
                state, 0, Direction.Stand, self.is_final_animation
            )
            return animation

    def __init__(self, draw_animations):
        self.states = {}
        self.draw_animations = draw_animations

    def get_animation_image(self, animation, animations):
        if animation.object not in self.states:
            if isinstance(animation.object, ExplosionBlock):
                self.states[animation.object] = \
                    StateSwitcher.ExplosionState(4, self._is_final_animation(
                        animation, animations
                    ))
            else:
                self.states[animation.object] = \
                    StateSwitcher.State()
        state = self.states[animation.object].switch_state(animation)
        return self.draw_animations[type(animation.object)] \
            .get_animation_image(animation, state)

    def _is_final_animation(self, animation, animations):
        location = animation.location + CELL_SIZE * animation.direction.value
        points = {anim.location
                  for anim in animations
                  if isinstance(anim.object, ExplosionBlock)}
        return location + animation.object.direction.value * CELL_SIZE \
               not in points

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

        def get_image(name):
            return Image(os.path.join("images", name))

        unbreakable_block_image = get_image("unbreakable_block.png")
        destroyable_block_image = get_image("destroyable_block.png")
        fortified_block_image = get_image("fortified_block.png")
        bomb_image = get_image("bomb.png")
        high_bomb_bonus_image = get_image("high_bomb_bonus.png")
        immune_bonus_image = get_image("immune_bonus.png")
        long_explosion_bonus_image = get_image("long_explosion_bonus.png")

        player_up_images = [get_image("player_up_0.png"),
                            get_image("player_up_1.png"),
                            get_image("player_up_2.png")]
        player_down_images = [get_image("player_down_0.png"),
                              get_image("player_down_1.png"),
                              get_image("player_down_2.png")]
        player_left_images = [get_image("player_left_0.png"),
                              get_image("player_left_1.png"),
                              get_image("player_left_2.png")]
        player_right_images = [get_image("player_right_0.png"),
                               get_image("player_right_1.png"),
                               get_image("player_right_2.png")]
        player_die_images = [get_image("player_die_0.png"),
                             get_image("player_die_1.png"),
                             get_image("player_die_2.png"),
                             get_image("player_die_3.png"),
                             get_image("player_die_4.png"),
                             get_image("player_die_5.png")]
        player_stand_image = get_image("player_down_0.png")

        simple_monster_left_images = [get_image("simple_monster_0.png"),
                                      get_image("simple_monster_1.png"),
                                      get_image("simple_monster_2.png")]
        simple_monster_right_images = [get_image("simple_monster_3.png"),
                                       get_image("simple_monster_4.png"),
                                       get_image("simple_monster_5.png")]
        simple_monster_down_images = [get_image("simple_monster_0.png"),
                                      get_image("simple_monster_1.png"),
                                      get_image("simple_monster_2.png")]
        simple_monster_up_images = [get_image("simple_monster_3.png"),
                                    get_image("simple_monster_4.png"),
                                    get_image("simple_monster_5.png")]
        simple_monster_die_images = [get_image("simple_monster_die_0.png"),
                                     get_image("simple_monster_die_1.png"),
                                     get_image("simple_monster_die_2.png"),
                                     get_image("simple_monster_die_3.png"),
                                     get_image("simple_monster_die_4.png")]
        simple_monster_stand_image = get_image("simple_monster_0.png")

        clever_monster_up_images = [get_image("clever_monster_0.png"),
                                    get_image("clever_monster_1.png"),
                                    get_image("clever_monster_6.png")]
        clever_monster_down_images = [get_image("clever_monster_2.png"),
                                      get_image("clever_monster_3.png"),
                                      get_image("clever_monster_4.png")]
        clever_monster_left_images = [get_image("clever_monster_0.png"),
                                      get_image("clever_monster_1.png"),
                                      get_image("clever_monster_6.png")]
        clever_monster_right_images = [get_image("clever_monster_2.png"),
                                       get_image("clever_monster_3.png"),
                                       get_image("clever_monster_4.png")]
        clever_monster_die_images = [get_image("clever_monster_die.png")]
        clever_monster_stand_image = get_image("clever_monster_0.png")

        strong_monster_up_images = [get_image("strong_monster_0.png"),
                                    get_image("strong_monster_1.png"),
                                    get_image("strong_monster_2.png")]
        strong_monster_down_images = [get_image("strong_monster_3.png"),
                                      get_image("strong_monster_4.png"),
                                      get_image("strong_monster_5.png")]
        strong_monster_left_images = [get_image("strong_monster_0.png"),
                                      get_image("strong_monster_1.png"),
                                      get_image("strong_monster_2.png")]
        strong_monster_right_images = [get_image("strong_monster_3.png"),
                                       get_image("strong_monster_4.png"),
                                       get_image("strong_monster_5.png")]
        strong_monster_die_images = [get_image("strong_monster_die.png")]
        strong_monster_stand_image = get_image("strong_monster_0.png")

        explosion_up_images = [get_image("explosion_up_2.png"),
                               get_image("explosion_up_1.png"),
                               get_image("explosion_up_0.png")]
        explosion_down_images = [get_image("explosion_down_2.png"),
                                 get_image("explosion_down_1.png"),
                                 get_image("explosion_down_0.png")]
        explosion_left_images = [get_image("explosion_left_2.png"),
                                 get_image("explosion_left_1.png"),
                                 get_image("explosion_left_0.png")]
        explosion_right_images = [get_image("explosion_right_2.png"),
                                  get_image("explosion_right_1.png"),
                                  get_image("explosion_right_0.png")]
        explosion_central_images = [get_image("explosion_center_2.png"),
                                    get_image("explosion_center_1.png"),
                                    get_image("explosion_center_0.png")]
        explosion_vertical_images = [get_image("explosion_vertical_2.png"),
                                     get_image("explosion_vertical_1.png"),
                                     get_image("explosion_vertical_0.png")]
        explosion_horizontal_images = [get_image("explosion_horizontal_2.png"),
                                       get_image("explosion_horizontal_1.png"),
                                       get_image("explosion_horizontal_0.png")]

        draw_animations = {
            UnbreakableBlock: DrawAnimation(unbreakable_block_image),
            DestroyableBlock: DrawAnimation(destroyable_block_image),
            FortifiedBlock: DrawAnimation(fortified_block_image),
            SimpleBomb: DrawAnimation(bomb_image),
            HighPowerBomb: DrawAnimation(bomb_image),
            HighBombBonus: DrawAnimation(high_bomb_bonus_image),
            ImmuneBonus: DrawAnimation(immune_bonus_image),
            LongExplosionBonus: DrawAnimation(long_explosion_bonus_image),
            Player: ActorDrawAnimation(player_left_images, player_right_images,
                                       player_down_images, player_up_images,
                                       player_stand_image, player_die_images),
            SimpleMonster: ActorDrawAnimation(simple_monster_left_images,
                                              simple_monster_right_images,
                                              simple_monster_up_images,
                                              simple_monster_down_images,
                                              simple_monster_stand_image,
                                              simple_monster_die_images),
            CleverMonster: ActorDrawAnimation(clever_monster_left_images,
                                              clever_monster_right_images,
                                              clever_monster_up_images,
                                              clever_monster_down_images,
                                              clever_monster_stand_image,
                                              clever_monster_die_images),
            StrongMonster: ActorDrawAnimation(strong_monster_left_images,
                                              strong_monster_right_images,
                                              strong_monster_up_images,
                                              strong_monster_down_images,
                                              strong_monster_stand_image,
                                              strong_monster_die_images),
            ExplosionBlock: ExplosionDrawAnimation(
                explosion_left_images,
                explosion_right_images,
                explosion_down_images,
                explosion_up_images,
                explosion_central_images,
                explosion_vertical_images,
                explosion_horizontal_images
            ),
            HighPoweredExplosion: ExplosionDrawAnimation(
                explosion_left_images,
                explosion_right_images,
                explosion_down_images,
                explosion_up_images,
                explosion_central_images,
                explosion_vertical_images,
                explosion_horizontal_images
            )
        }
        self.state_switcher = StateSwitcher(draw_animations)


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
        return self.state_switcher.get_animation_image(animation, animations)


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
