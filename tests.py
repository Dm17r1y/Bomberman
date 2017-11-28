#!/usr/bin/python3

import unittest
from logic import *
import child_classes
import level_creator


class GoRightController(PlayerController):

    def select_action(self):
        return Move(Direction.Right)


class GoLeftController(PlayerController):

    def select_action(self):
        return Move(Direction.Left)


class GoUpController(PlayerController):

    def select_action(self):
        return Move(Direction.Up)


class GoDownController(PlayerController):

    def select_action(self):
        return Move(Direction.Down)


class EmptyGameController(GameController):

    def select_action(self):
        return Move(Direction.Up)


class MovementTests(unittest.TestCase):

    def setUp(self):
        self.player = Player(GoRightController())
        self.map = Map()
        self.map.add_map_object(self.player, Point(0, 0))
        self.game = Game(self.map, EmptyGameController(), self.player)

    def test_correct_initialization(self):
        self.assertEqual(self.player, self.game.player)
        self.assertEqual(1, len(self.map.get_map_objects(Point(0, 0))))
        self.assertEqual(self.map, self.game._map)
        self.assertEqual(self.player, self.map.get_map_objects(Point(0, 0))[0])
        self.assertEqual(self.map._objects, {Point(0, 0): [self.player]})
        self.assertEqual({Point(0, 0)}, self.map.occupied_cells)

    def test_movement(self):
        self.game.make_turn()
        self.assertEqual(0, len(self.game._map.get_map_objects(Point(0, 0))))
        self.assertEqual(1, len(self.game._map.get_map_objects(Point(1, 0))))
        self.assertEqual(self.player,
                         self.game._map.get_map_objects(Point(1, 0))[0])

    def test_move_player_to_block(self):
        self.map.add_map_object(Block(), Point(CELL_WIDTH, 0))
        self.game.make_turn()
        self.assertEqual(1, len(self.game._map.get_map_objects(Point(0, 0))))
        self.assertEqual(0, len(self.game._map.get_map_objects(Point(1, 0))))
        self.assertEqual(self.player,
                         self.game._map.get_map_objects(Point(0, 0))[0])

    def test_remove_dead_objects(self):
        self.player._is_dead = True
        self.game.make_turn()
        self.assertEqual(set(), self.game.map.occupied_cells)


class PlayerCollisionTests(unittest.TestCase):

    def setUp(self):
        self.map = Map()
        self.player = Player(GoRightController())
        self.game = Game(self.map, EmptyGameController(), self.player)
        self.map.add_map_object(self.player, Point(0, 0))

    def test_collision_player_and_monster(self):
        monster = Monster()
        self.map.add_map_object(monster, Point(CELL_WIDTH, 0))
        self.assertEqual(False, self.player.is_dead)
        self.game.make_turn()
        self.assertEqual(True, self.player.is_dead)
        self.assertEqual(False, monster.is_dead)

    def test_collision_actor_and_explosion(self):
        explosion = ExplosionBlock(10)
        self.map.add_map_object(explosion, Point(0, 0))
        monster = Monster()
        self.map.add_map_object(monster, Point(0, 0))
        self.game.make_turn()
        self.assertNotIn(monster, self.game._map.get_map_objects(Point(0, 0)))
        self.assertEqual(True, monster.is_dead)
        self.assertEqual(True, self.player.is_dead)
        self.assertEqual(False, explosion.is_dead)

    def test_collision_player_and_bonus(self):
        coordinates = Point(0, 0)
        bonus = Bonus()
        self.map.add_map_object(bonus, coordinates)
        self.game.make_turn()
        self.assertEqual(True, bonus.is_dead)
        self.assertEqual(False, self.player.is_dead)


class PutBombController(PlayerController):

    def select_action(self):
        return PutBomb(Bomb(1, 5))


class BombAndExplosionTests(unittest.TestCase):

    def setUp(self):
        self.map = Map()
        self.player = Player(PutBombController())
        self.game = Game(self.map, EmptyGameController(), self.player)

    def test_explose_bomb(self):
        bomb = Bomb(1, 5)
        self.map.add_map_object(bomb, Point(0, 0))
        self.game.make_turn()
        self.assertEqual(True, bomb.is_dead)
        for i in range(1, 5):
            for direction in (Direction.Up, Direction.Down,
                              Direction.Right, Direction.Left):
                point = direction.value * CELL_WIDTH * i
                self.assertEqual(1, len(self.game._map.get_map_objects(point)))
                self.assertEqual(ExplosionBlock,
                                 type(self.game._map
                                      .get_map_objects(point)[0]))

    def test_stop_fire(self):
        explosion = ExplosionBlock(2)
        self.map.add_map_object(explosion, Point(0, 0))
        self.game.make_turn()
        self.assertEqual(False, explosion.is_dead)
        self.game.make_turn()
        self.assertEqual(True, explosion.is_dead)

    def test_stop_explosion(self):
        block = Block()
        self.map.add_map_object(block, Point(0, CELL_WIDTH))
        bomb = Bomb(1, 5)
        self.map.add_map_object(bomb, Point(0, 0))
        self.game.make_turn()
        self.assertIn(block, self.game._map
                      .get_map_objects(Point(0, CELL_WIDTH)))
        self.assertEqual(0, len(self.game._map
                                .get_map_objects(Point(0, CELL_WIDTH * 2))))

    def test_player_can_walk_trough_placed_bomb(self):

        class PutBombAndMoveController(PlayerController):

            def __init__(self):
                self.is_first = True

            def select_action(self):
                if self.is_first:
                    self.is_first = False
                    return PutBomb(Bomb(10, 10))
                else:
                    return Move(Direction.Right)

        player = Player(PutBombAndMoveController())
        self.map.add_map_object(player, Point(0, 0))
        self.game.make_turn()
        self.game.make_turn()
        self.assertEqual([player], self.game._map.get_map_objects(Point(1, 0)))
        self.assertEqual([Bomb], list(map(type, self.game._map
                                          .get_map_objects(Point(0, 0)))))

    def test_player_cant_put_bomb(self):
        bomb = Bomb(10, 10)
        self.map.add_bomb(bomb, Point(0, 0))
        self.map.add_map_object(self.player, Point(0, 0))
        self.game.make_turn()
        self.assertEqual(2, len(self.game._map._objects[Point(0, 0)]))
        self.assertIn(bomb, self.game._map._objects[Point(0, 0)])
        self.assertIn(self.player, self.game._map._objects[Point(0, 0)])


class OtherTests(unittest.TestCase):

    def setUp(self):
        self.map = Map()
        self.player = Player(PutBombController())
        self.game = Game(self.map, EmptyGameController(), self.player)

    def test_apply_bomb(self):
        self.map.add_map_object(self.player, Point(29, 33))
        self.game.make_turn()
        self.assertIn(Bomb, list(map(type, self.game._map
                                     .get_map_objects(Point(32, 32)))))

    def test_pass_corner(self):
        self.map.add_map_object(Block(), Point(32, 32))
        player = Player(GoRightController())
        self.map.add_map_object(player,
                                Point(32 - CELL_WIDTH,
                                      32 - CELL_WIDTH + CORNER_SIZE))
        self.game.make_turn()
        self.assertEqual([player],
                         self.game._map.get_map_objects(
                             Point(32 - CELL_WIDTH,
                                   32 - CELL_WIDTH + CORNER_SIZE - 1))
                         )

    def test_animations(self):
        player = Player(GoRightController())
        self.map.add_map_object(player, Point(0, 0))
        self.map.add_map_object(Block(), Point(32, 32))
        animations = self.game.make_turn()
        self.assertEqual(2, len(animations))
        self.assertIn(Player, map(type, (anim.object for anim in animations)))
        self.assertIn(Block, map(type, (anim.object for anim in animations)))

    def test_player_sets_controller(self):
        controller = GoRightController()
        player = Player(controller)
        self.assertEqual(player, controller._player)

    def test_level_creator(self):
        legend = {
            '#': lambda: (Block(),),
            '*': lambda: (Player(GoRightController()),),
            '1': lambda: (Monster(),)
        }
        level_creator_ = level_creator.LevelCreator(legend)
        level = [
            "# # # # # # # # # # ",
            "1#1#1#1#1#1#1#1#1#1#",
            "* * * * * * * * * * "
        ]
        game_map = level_creator_.create_level(level)
        for i in range(10):
            self.assertEqual(Block, type(game_map.get_map_objects(
                Point(i * CELL_WIDTH * 2, 0)
            )[0]))
            self.assertEqual(0, len(game_map.get_map_objects(
                Point(i * CELL_WIDTH * 2 + CELL_WIDTH, 0)
            )))
            self.assertEqual(Monster, type(game_map.get_map_objects(
                Point(i * CELL_WIDTH * 2, CELL_WIDTH)
            )[0]))
            self.assertEqual(Block, type(game_map.get_map_objects(
                Point(i * CELL_WIDTH * 2 + CELL_WIDTH, CELL_WIDTH)
            )[0]))
            self.assertEqual(Player, type(game_map.get_map_objects(
                Point(i * CELL_WIDTH * 2, CELL_WIDTH * 2)
            )[0]))
            self.assertEqual(0, len(game_map.get_map_objects(
                Point(i * CELL_WIDTH * 2 + CELL_WIDTH, CELL_WIDTH * 2)
            )))


class TestChildClasses(unittest.TestCase):

    def setUp(self):
        self.map = Map()
        self.player = Player(GoRightController())
        self.game = Game(self.map, GameController(), self.player)

    def test_simple_monster(self):
        monster = child_classes.SimpleMonster()
        self.map.add_map_object(monster, Point(CELL_WIDTH, CELL_WIDTH))
        self.map.add_map_object(Block(), Point(CELL_WIDTH, 0))
        self.map.add_map_object(Block(), Point(0, CELL_WIDTH))
        self.map.add_map_object(Block(), Point(CELL_WIDTH, CELL_WIDTH * 2))
        self.game.make_turn()
        self.assertEqual([monster], self.game._map
                         .get_map_objects(Point(CELL_WIDTH + 1, CELL_WIDTH)))
        self.assertEqual(Direction.Right, monster.direction)

    def test_clever_monster(self):
        legend = {
            '*': lambda: (Player(GoRightController()),),
            '#': lambda: (Block(),),
            '0': lambda: (child_classes.CleverMonster(),)
        }
        level_creator_ = level_creator.LevelCreator(legend)
        self.map = level_creator_.create_level([
            "#####",
            "#0  #",
            "# # #",
            "###*#"
        ])
        self.game = Game(self.map, GameController(),
                         Player(GoRightController()))
        self.game.make_turn()
        self.assertEqual(child_classes.CleverMonster,
                         type(self.game.map.get_map_objects(
                             Point(CELL_WIDTH + 1, CELL_WIDTH)
                         )[0]))

    def test_new_monsters_kill_player(self):
        self.map.add_map_object(self.player, Point(0, 0))
        self.map.add_map_object(child_classes.SimpleMonster(), Point(0, 0))
        self.game.make_turn()
        self.assertTrue(self.player.is_dead)

    def test_strong_monster(self):
        monster = child_classes.StrongMonster()
        self.map.add_map_object(monster, Point(0, 0))
        self.map.add_map_object(ExplosionBlock(100), Point(0, 0))
        self.game.make_turn()
        self.assertFalse(monster.is_dead)
        self.game.map.add_map_object(child_classes.HighPoweredExplosion(100),
                                     Point(0, 0))
        self.game.make_turn()
        self.assertTrue(monster.is_dead)

    def test_destroy_stone_block(self):
        stone_block = child_classes.FortifiedBlock()
        self.map.add_map_object(stone_block, Point(0, 0))
        self.map.add_map_object(ExplosionBlock(100), Point(0, 0))
        self.game.make_turn()
        self.assertFalse(stone_block.is_dead)
        self.game.map.add_map_object(child_classes.HighPoweredExplosion(100),
                                     Point(0, 0))
        self.game.make_turn()
        self.assertTrue(stone_block.is_dead)

    def test_destroy_brick_block(self):
        brick_block = child_classes.DestroyableBlock()
        self.map.add_map_object(brick_block, Point(0, 0))
        self.map.add_map_object(ExplosionBlock(100), Point(0, 0))
        self.game.make_turn()
        self.assertTrue(brick_block.is_dead)

    def test_high_explosion_bonus(self):
        self.assertEqual(Bomb, type(self.player.get_bomb()))
        self.player.set_bomb_type(child_classes.SimpleBomb)
        self.assertEqual(child_classes.SimpleBomb,
                         type(self.player.get_bomb()))

    def test_long_explosion_bonus(self):
        self.assertEqual(START_EXPLOSION_RADIUS,
                         self.player.get_bomb()._explosion_radius)
        self.player.set_bomb_radius(10)
        self.assertEqual(10, self.player.get_bomb()._explosion_radius)

    def test_immune_buff(self):
        self.map.add_map_object(self.player, Point(0, 0))
        immune_buff = child_classes.ImmuneBuff()
        immune_buff.time = 2
        self.player.add_buff(immune_buff)
        self.map.add_map_object(Monster(), Point(0, 0))
        self.game.make_turn()
        self.assertFalse(self.player.is_dead)
        self.game.make_turn()
        self.assertTrue(self.player.is_dead)

    def test_player_cannot_move_to_destroyable_block(self):
        self.map.add_map_object(self.player, Point(0, 0))
        self.map.add_map_object(
            child_classes.DestroyableBlock(),
            Point(CELL_WIDTH, 0)
        )
        self.game.make_turn()
        self.assertEqual(0, len(self.game._map.get_map_objects(
            Point(1, 0)
        )))
        self.assertEqual([self.player], self.game._map.get_map_objects(
            Point(0, 0)
        ))


if __name__ == "__main__":
    unittest.main()
