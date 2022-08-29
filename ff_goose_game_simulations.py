from math import ceil
from progressbar import progressbar #pip install progressbar2
from random import randint
from statistics import median, mode
from typing import Union


class S:
  EMPTY = 0
  POINTS = 1
  ADD_DIE = 2
  GACHA = 3
  CAT = 4
  ADD_WISH = 5


class Gacha:
  DOUBLE_DIE_VALUE = 0
  HALVE_DIE_VALUE = 1
  SQUARE_ONE = 2
  DOUBLE_NEXT_EARNINGS = 3
  EXTRA_10_PTS = 4
  ADD_WISH = 5
  
  def __init__(self):
    self.reset()

  def pull(self):
    self.gacha = self.gacha or list(range(6))
    return self.gacha.pop( randint(0, len(self.gacha)-1) )

  def reset(self):
    self.gacha = list(range(6))


class Board:
  __BOARD = [0,0,0,S.POINTS,S.ADD_DIE,0,0,0,0,S.GACHA,S.POINTS,0,0,0,S.CAT,0,0,S.POINTS,0,S.ADD_WISH]
  BOARD_SIZE = len(__BOARD)
  LAST_CELL_POS = BOARD_SIZE - 1
  POINT_INDICES = [3, 10, 17]
  EXTRA_DICE = [4, 19]
  STARTING_POINTS = 2
  MAX_POINTS = 4
  
  def __init__(self, starting_dice:int =0, starting_wish:int =0):
    self.gacha = Gacha()
    self.cell_values = [0]*Board.BOARD_SIZE
    self.starting_dice = starting_dice
    self.starting_wish = starting_wish
    self.reset()
  
  def reset(self, pos:int =-1, starting_points:int =-1):
    self.gacha.reset()
    self.score = 0
    self.score_mod = 1
    self.dice = self.starting_dice
    self.wish = self.starting_wish
    self.nb_used_dice = 0
    self.nb_used_wish = 0
    self.new_pos = self.pos = Board.BOARD_SIZE-1 if -1==pos else pos
    self.offset_pos = 0
    self.move_mod = 1
    for index in Board.POINT_INDICES:
      self.cell_values[index] = Board.STARTING_POINTS if starting_points==-1 else starting_points

  def inc_cell_value(self, index:int =-1):
    if index == -1: index = self.new_pos
    self.cell_values[index] = min(Board.MAX_POINTS, self.cell_values[index]+1)

  def cell(self, index:int =-1):
    if index == -1:
      index = self.new_pos
    return Board.__BOARD[index]
  

  def update_score(self):
    if self.new_pos < self.pos:
      score = ((  sum(self.cell_values[self.pos+1 : ])
                + sum(self.cell_values[0 : self.new_pos+1]))
                * self.score_mod)
    else:
      score = sum(self.cell_values[self.pos+1 : self.new_pos+1]) * self.score_mod
    self.score_mod = 1
    self.score += score


  def use_dice(self):
    if self.dice == 0:
      return 0 if self.wish <= 0 else self.use_wish()
    return self.move(randint(1,6))


  def use_wish(self, desired_result:int = -1):
    if self.wish == 0:
      return 0 if self.dice <= 0 else self.use_dice()
    #TODO: compute most desired result
    if desired_result == -1:
      desired_result = 6
    return self.move(desired_result, True)


  def move(self, dice_result:int, is_wish:bool =False):
    #reroll cat landing
    MAX_CAT_REROLL = 1
    nb_cat_reroll = 0
    #while :
    while True:
      move_by = ceil(dice_result * self.move_mod)
      self.new_pos = (self.pos + move_by) % Board.BOARD_SIZE
      if (nb_cat_reroll != MAX_CAT_REROLL  or
          self.cell(self.new_pos) != S.CAT):
        break
      nb_cat_reroll += 1
      dice_result = randint(1,6)
        
    self.move_mod = 1    
    self.offset_pos = 0
    
    match cell := self.cell(self.new_pos):
      case S.ADD_DIE:
        self.dice += 1
      case S.ADD_WISH:
        self.wish += 1
      case S.CAT:
        self.offset_pos = randint(-4,-1)
    
    self.update_score(cell)
    
    match cell:
      case S.POINTS:
        #landing on points cell increases value AFTER adding to score
        self.inc_cell_value()
      case S.GACHA:
        match self.gacha.pull():
          case Gacha.DOUBLE_DIE_VALUE:    self.move_mod = 2
          case Gacha.HALVE_DIE_VALUE:     self.move_mod = 0.5
          case Gacha.SQUARE_ONE:          self.offset_pos = Board.LAST_CELL_POS - self.new_pos
          case Gacha.DOUBLE_NEXT_EARNINGS:self.score_mod = 2
          case Gacha.EXTRA_10_PTS:        self.score += 10
          case Gacha.ADD_WISH:            self.wish += 1
    
    if is_wish:
      self.nb_used_wish += 1
      self.wish -= 1
    else:
      self.nb_used_dice += 1
      self.dice -= 1
    
    self.pos = self.new_pos + self.offset_pos
    return self.dice + self.wish
  
  
  # def can_reach_next_score_cell(self):
  #   if self.wish > 1:
  #   if self.pos > 1:
  #     pass
  #   Board.POINT_INDICES


  def use_right_dice(self):
    [extra_dice_pos, extra_wish_pos] = Board.EXTRA_DICE
    # within range of extra wish dice cell ?
    from_extra_wish = extra_wish_pos - self.pos
    if self.wish > 0 and from_extra_wish > 0 and from_extra_wish <= 6*self.move_mod:
      return self.move(from_extra_wish, True)
    from_extra_dice = extra_dice_pos - self.pos + (
      0 if self.pos<extra_dice_pos else Board.BOARD_SIZE)
    # within range of extra dice cell ?
    # go if 2+ wishes or 1 and can't complete another run
    if (self.wish > 1 or self.wish == 1 and self.dice < 5) and from_extra_dice <= 6:
      return self.move(from_extra_dice, True)
    return self.move(randint(1,6))


  def nb_dice_required(self, target_score:int, pos:int =-1, nb_wish:int =1):
    self.reset(pos, 4)
    self.pos = pos
    self.dice = 999_999
    self.wish = nb_wish
    while self.score < target_score:
      self.use_right_dice()
    return self.nb_used_dice



def play_from_start(board:Board, show_stats:bool= 0):
  board.reset()
  used_dice = 0
  laps = 0
  prev_pos = -1

  while board.dice + board.wish > 0:
    board.use_right_dice()
    if board.pos < prev_pos: laps += 1
    prev_pos = board.pos
    used_dice += 1
  
  if show_stats:
    print(f"{board.score:^7}", end='')
    print(f"{used_dice:^7}", flush=1)
  
  return board.score, used_dice


def req_extra(req_dice:Union[int,float], nb_decimals:int =0):
  if req_dice > 0:
    return f"Req. {req_dice:.{nb_decimals}f} more dice"
  elif req_dice > 0:
    return f"Surplus of {req_dice:.{nb_decimals}f} dice"
  return f"Exact amount!"


def run_simul_nb_dice_required(
  nb_runs: int,
  target_score: int,
  currency_levels: list[int],
  pos: int = -1,
  nb_wish: int = 1,
  nb_dice: int = 0,
  ):
  board = Board()
  for i, ipts in enumerate(Board.POINT_INDICES):
    board.cell_values[ipts] = currency_levels[i]+1
  results = [0]*nb_runs
  for i in progressbar(range(nb_runs)):
    results[i] = board.nb_dice_required(target_score, pos= pos, nb_wish= nb_wish)
    #results[i] = max(0, board.nb_dice_required(target_score, pos= pos, nb_wish= nb_wish)-nb_dice)
  
  rmin, rmax = min(results), max(results)
  rsum, rmed = sum(results), median(results)
  ravg, rmod = rsum/nb_runs, mode(results)
  print(f"Nb dice required to reach {target_score}:")
  print(f"min-max: {f'{rmin}-{rmax}':>6}  [{f'{rmin-nb_dice} to {rmax-nb_dice}':^6}]")
  print(f"average: {ravg:>6.2f}  [{req_extra(ravg-nb_dice,2):>6}]")
  print(f"median:  {rmed:>6.2f}  [{req_extra(rmed-nb_dice,1):>6}]")
  print(f"mode:    {rmod:>6.2f}  [{req_extra(rmod-nb_dice):>6}]")


class TaskType:
  NB_DICE_REQUIRED_TO_REACH_SCORE = 1
  SCORE_FROM_AVAILABLE_DICE = 2

#TODO:
#class Priority:
#  WISH_TO_UPGRADE_POINTS = 1
#  threashold = 2

if __name__ == "__main__":
  # select task to run
  task_to_run = TaskType.NB_DICE_REQUIRED_TO_REACH_SCORE
  #task_to_run = TaskType.SCORE_FROM_AVAILABLE_DICE
  
  match task_to_run:
    case TaskType.NB_DICE_REQUIRED_TO_REACH_SCORE:
      run_simul_nb_dice_required(
        nb_runs= 1_000,
        currency_levels= [3,3,3], # 1, 2 or 3
        target_score= 36,
        pos= 16, #Heart 16 #Ara 
        nb_wish= 1+2, #Heart 3 #Ara 3
        #inventory + board_rewards + daily_rewards + quest*3 + daily selection (+ 4th quest)
        nb_dice= 15, #Heart 15 #Ara 5
      )
    # WIP
    case TaskType.SCORE_FROM_AVAILABLE_DICE:
      NB_RUNS = 1_000
      DICE_PER_RUN = 50
      WISH_PER_RUN = 0
      STATS_PER_RUN = False
      board = Board(
        starting_dice= DICE_PER_RUN,
        starting_wish=  WISH_PER_RUN
        #TODO: simulate daily progress by injecting dice/wish from:
        #   - board rewards
        #   - daily selection shop
        #   - natural quests progress
        #  depending if in "hoard mode" and not (fine tune thresholds)
      )
      scores = [0]*NB_RUNS
      if STATS_PER_RUN: print(f"{'score':^7}{'#dice':^7}")
      for i in progressbar(range(NB_RUNS)):
        scores[i], _ = play_from_start(board, STATS_PER_RUN)

      print(f"Score reached with {DICE_PER_RUN} dice and {WISH_PER_RUN} wish:")
      print(f"min-max range: [{min(scores)}-{max(scores)}]")
      print(f"average: {sum(scores)/NB_RUNS:>6.2f}")
      print(f"median:  {median(scores):>6.2f}")
      print(f"mode:    {mode(scores):>6.2f}")