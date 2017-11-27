#!/usr/bin/python3

from PyQt5 import QtWidgets, QtGui, QtCore
import sys
from logic import CELL_WIDTH
import logic
from point import Direction
from controller import *

TIMER_DELAY_MILLISECONDS = 20

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
        if self._key:
            return actions[self._key]
        return logic.Move(Direction.Stand)

    def set_key(self, key):
        self._key = key

    def release_key(self):
        self._key = None


class BombermanWindow(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.view = BombermanView(self)
        self.initialize_game()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.make_turn)
        self.timer.start(TIMER_DELAY_MILLISECONDS)
        self.resize(30 * CELL_WIDTH, 30 * CELL_WIDTH)
        self.show()

    def make_turn(self):
        animations = self.game.make_turn()
        self.view.animate(animations)

    def initialize_game(self):
        game_map = logic.Map()
        self.controller = PlayerController(200, 5)
        player = logic.Player(self.controller)
        game_map.add_map_object(player, logic.Point(0, 0))
        game_map.add_map_object(logic.Block(), logic.Point(32, 32))
        self.game = logic.Game(game_map, GameController(), player)

    def keyPressEvent(self, key_event):
        self.controller.set_key(key_event.key())

    def keyReleaseEvent(self, QKeyEvent):
        self.controller.release_key()


class BombermanView(QtWidgets.QGraphicsView):

    def __init__(self, window):
        super().__init__(window)
        self.add_scene()
        self.load_images()

    def load_images(self):

        class AnimationImage(QtWidgets.QGraphicsWidget):
            def __init__(self, image):
                super().__init__()
                self.image = image

            def paint(self, painter, style, widget=None):
                painter.drawPixmap(QtCore.QPointF(), self.image)

        class Image:
            def __init__(self, path_to_image):
                self.image = QtGui.QPixmap(path_to_image) \
                    .scaled(CELL_WIDTH, CELL_WIDTH)

            def get_animation_image(self):
                return AnimationImage(self.image)

        block_stone_image = Image("images/block_stone.png")
        block_brick_image = Image("images/block_brick.png")
        player_image = Image("images/player.png")
        bomb_image = Image("images/bomb.png")
        explosion_central_image = Image("images/explosion_center.png")
        explosion_right_image = Image("images/explosion_right.png")
        explosion_left_image = Image("images/explosion_left.png")
        explosion_up_image = Image("images/explosion_up.png")
        explosion_down_image = Image("images/explosion_down.png")
        explosion_vertical_image = Image("images/explosion_vertical.png")
        explosion_horizontal_image = Image("images/explosion_horizontal.png")
        monster_image = Image("images/monster.png")

        self.images = {logic.Block: block_stone_image,
                       logic.Player: player_image,
                       logic.Bomb: bomb_image,
                       logic.Monster: monster_image}

        self.explosion_images = {
            logic.Direction.Up: explosion_down_image,
            logic.Direction.Down: explosion_up_image,
            logic.Direction.Left: explosion_left_image,
            logic.Direction.Right: explosion_right_image
        }
        self.explosion_vertical_image = explosion_vertical_image
        self.explosion_horizontal_image = explosion_horizontal_image
        self.explosion_central_image = explosion_central_image

    def add_scene(self):
        scene = QtWidgets.QGraphicsScene(0, 0, CELL_WIDTH * 30,
                                         CELL_WIDTH * 30)
        scene.setBackgroundBrush(QtCore.Qt.cyan)
        self.setScene(scene)

    def animate(self, animations):
        scene = self.scene()
        scene.clear()
        self.parallel_animations = QtCore.QParallelAnimationGroup()
        for anim in animations:
            animation = self.get_object_animation(anim, animations)
            scene.addItem(animation.targetObject())
            self.parallel_animations.addAnimation(animation)
        self.parallel_animations.start()

    def get_object_animation(self, animation, animations):
        animation_item = self.get_animation_item(animation, animations)
        animation_ = QtCore.QPropertyAnimation(animation_item, b"geometry")
        animation_.setDuration(TIMER_DELAY_MILLISECONDS)
        start_rect = QtCore.QRect(animation.location.x,
                                  animation.location.y,
                                  CELL_WIDTH, CELL_WIDTH)
        new_coordinates = animation.location + animation.direction.value
        end_rect = QtCore.QRect(new_coordinates.x,
                                new_coordinates.y,
                                CELL_WIDTH, CELL_WIDTH)
        animation_.setStartValue(start_rect)
        animation_.setEndValue(end_rect)
        return animation_

    def get_animation_item(self, animation, animations):

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
                if animation.location + (direction.value * CELL_WIDTH)\
                        in animation_points:
                    neighboring_explosions.append(direction)

            if len(neighboring_explosions) == 1:
                return self.explosion_images[
                    opposite[neighboring_explosions[0]]
                ].get_animation_image()
            elif len(neighboring_explosions) == 2:
                if set(neighboring_explosions) == \
                        {Direction.Up, Direction.Down}:
                    return self.explosion_vertical_image.get_animation_image()
                elif set(neighboring_explosions) == \
                        {Direction.Left, Direction.Right}:
                    return self.explosion_horizontal_image\
                        .get_animation_image()
            return self.explosion_central_image.get_animation_image()
        else:
            return self.images[type(animation.object)].get_animation_image()

class MainWindow(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        start_button = QtWidgets.QPushButton("Start")
        start_button.clicked.connect(self.start)
        layout.addWidget(start_button)
        self.setLayout(layout)
        self.show()

    def start(self):
        self.window = BombermanWindow()


def main():
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()