from bb_ai_12_police.domain.barriers import BarrierSet
from bb_ai_12_police.domain.board import Board
from bb_ai_12_police.domain.protocol import Direction, Position


def test_board_from_config():
    board = Board.from_config({"board_and_agents": {"grid_size": 7}})
    assert board.size == 7


def test_barrier_set_from_config():
    barriers = BarrierSet.from_config({"movement_and_barriers": {"max_barriers": 2}})
    assert barriers.max_barriers == 2
    assert barriers.remaining == 2


def test_barrier_cannot_place_on_already_placed_cell():
    board = Board(size=7)
    barriers = BarrierSet(max_barriers=14)
    cop = Position(3, 3)
    barriers.place(Position(3, 4), cop, board)
    assert not barriers.can_place(Position(3, 4), cop, board)


def test_board_neighbors_returns_all_five_directions():
    board = Board(size=7)
    neighbors = board.neighbors(Position(3, 3))
    assert set(neighbors.keys()) == set(Direction)
    assert neighbors[Direction.STAY] == Position(3, 3)
