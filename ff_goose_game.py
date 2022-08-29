from math import ceil, floor
from re import T
from progressbar import progressbar #pip install progressbar2
from random import randint
from statistics import median, mode
from typing import Union


class S:
  EMPTY = 0 # Gold, Tickets, FULI Wishes, etc...
  CURRENCY = 1 # Eyepatch / Baseball
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


#TODO: make it a real class to fine tune wish usage
#      and weight different options/priorities
class WishUsagePriority:
  EXTRA_WISH = 0 # default
  UPGRADES = 1 #TODO: to implement
  GACHA = 2
  #upgrade_levels_threashold = 2
  def print(wish_usage_priority:int):
    return  { WishUsagePriority.EXTRA_WISH: "Extra Wish",
              WishUsagePriority.UPGRADES: "Eyepatch/Baseball levels",
              WishUsagePriority.GACHA: "Gacha machine",
            }.get(wish_usage_priority, "")


class Board:
  __BOARD = [0,0,0,S.CURRENCY,S.ADD_DIE,0,0,0,0,S.GACHA,S.CURRENCY,0,0,0,S.CAT,0,0,S.CURRENCY,0,S.ADD_WISH]
  BOARD_SIZE = len(__BOARD)
  LAST_CELL_POS = BOARD_SIZE - 1
  CURRENCY_INDICES = [3, 10, 17]
  MIN_CURRENCY_LEVEL = 1
  MAX_CURRENCY_LEVEL = 3
  BASE_CURRENCY_LEVELS = [MIN_CURRENCY_LEVEL]*len(CURRENCY_INDICES)
  EXTRA_DICE = [4, 19]
  
  def __init__(
    self,
    starting_dice:int =0,
    starting_wish:int =0,
    starting_currency_levels =1, # int or list[int]
  ):
    self.gacha = Gacha()
    self.starting_dice = starting_dice
    self.starting_wish = starting_wish
    
    if not starting_currency_levels:
      starting_currency_levels = Board.BASE_CURRENCY_LEVELS
    elif type(starting_currency_levels) is int:
      starting_currency_levels = [starting_currency_levels]*len(Board.CURRENCY_INDICES)
    elif type(starting_currency_levels) is not list:
      raise TypeError("test")
    self.starting_currency_levels = starting_currency_levels
    self.currency_levels = dict(zip(Board.CURRENCY_INDICES, starting_currency_levels))
    self.reset()


  def reset(self, pos:int =-1):
    self.gacha.reset()
    for square_pos, level in zip(self.currency_levels, self.starting_currency_levels):
      self.currency_levels[square_pos] = level
    self.score = 0
    self.score_mod = 1
    self.dice = self.starting_dice
    self.wish = self.starting_wish
    
    # for statistics
    self.nb_used_dice = 0
    self.nb_used_wish = 0
    self.nb_currency_landing = 0
    self.nb_gacha_landing = 0
    self.nb_extra_wish_landing = 0
    self.nb_extra_die_landing = 0
    self.nb_cat_landing = 0
    
    self.new_pos = self.pos = Board.BOARD_SIZE-1 if -1==pos else pos
    self.offset_pos = 0
    self.move_mod = 1


  def inc_currency_level(self, index:int =-1):
    if index == -1: index = self.new_pos
    self.currency_levels[index] = min(
      Board.MAX_CURRENCY_LEVEL,
      self.currency_levels[index] + 1)


  def cell(self, index:int =-1):
    if index == -1:
      index = self.new_pos
    return Board.__BOARD[index]
  

  def update_score(self):
    score = 0
    if self.new_pos < self.pos:
      for i, lv in self.currency_levels.items():
        if self.new_pos >= i or self.pos < i and self.new_pos < i:
          score += lv + 1
    else:
      for i, lv in self.currency_levels.items():
        if self.pos < i and self.new_pos >= i:
          score += lv + 1
    self.score += score * self.score_mod
    self.score_mod = 1


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
        self.nb_extra_die_landing += 1
        self.dice += 1
      case S.ADD_WISH:
        self.nb_extra_wish_landing += 1
        self.wish += 1
      case S.CAT:
        self.nb_cat_landing += 1
        self.offset_pos = randint(-4,-1)
    
    self.update_score()
    
    match cell:
      case S.CURRENCY:
        self.nb_currency_landing += 1
        #landing on points cell increases value AFTER adding to score
        self.inc_currency_level()
      case S.GACHA:
        self.nb_gacha_landing += 1
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

  def can_reach(self, target_pos:int, from_pos:int =-1):
    """Returns the distance if reachable or 0/False."""
    from_pos = self.pos if from_pos == -1 else from_pos
    distance = (target_pos - from_pos) % Board.BOARD_SIZE
    return distance <= ceil(6*self.move_mod) and distance
    

  def use_right_dice(self, wish_usage_priority1:int =WishUsagePriority.EXTRA_WISH):
    [extra_dice_pos, extra_wish_pos] = Board.EXTRA_DICE
    GACHA_POS = 9
    
    wish_req_offset = 0
    low_dice_offset = -2
    if wish_usage_priority1 == WishUsagePriority.GACHA:
      dist_gacha = self.can_reach(GACHA_POS)
      if self.wish > 0 and dist_gacha:
        return self.move(dist_gacha/self.move_mod, True)
      wish_req_offset = 1
      low_dice_offset = -2
      
    #TODO: function for cheching "self.wish" conditions:
    #  - if priority is set to GACHA and the check is about EXTRA_WISH, add 1
    #  - if remaining "self.wish" is low or "self.score" is nearing goal, remove 1
    #  - adjust what's considered a low amount of dice depending on position and priorities
    
    # within range of extra wish cell ?
    dist_extra_wish = self.can_reach(extra_wish_pos)
    if self.wish > wish_req_offset and dist_extra_wish:
      return self.move(dist_extra_wish/self.move_mod, True)
    dist_extra_dice = self.can_reach(extra_dice_pos)
    # within range of extra dice cell ?
    # go if 2+ wishes or 1 and can't complete another run
    if (self.wish > 1 or self.wish == 1+wish_req_offset and self.dice < 5+low_dice_offset) and dist_extra_dice <= 6:
      return self.move(dist_extra_dice/self.move_mod, True)
    return self.move(randint(1,6))


  def nb_dice_required(
    self,
    target_score:int,
    wish_usage_priority:int =WishUsagePriority.EXTRA_WISH,
    pos:int =-1,
    nb_wish:int =1,
  ):
    self.reset(pos)
    self.pos = pos
    self.dice = 999_999
    self.wish = nb_wish
    while self.score < target_score:
      self.use_right_dice(wish_usage_priority)
    return self.nb_used_dice - self.nb_extra_die_landing


def fmt_dice_req(req_dice:Union[int,float], nb_decimals:int =0):
  if req_dice > 0:
    return f"Requires {ceil(req_dice)} more dice"
  elif req_dice < 0:
    return f"Surplus of {floor(-req_dice)} dice"
  return f"Exact amount!"


def run_simu_nb_dice_required(
  nb_runs: int,
  target_score: int,
  currency_levels =None, # list[int] or int
  wish_usage_priority: int = WishUsagePriority.EXTRA_WISH,
  pos: int = -1,
  nb_wish: int = 1,
  nb_dice: int = 0,
  ):
  board = Board(starting_currency_levels= currency_levels)
  
  results = [0]*nb_runs
  nb_extra_die_landing = [0]*nb_runs
  nb_extra_wish_landing = [0]*nb_runs
  nb_cat_landing = [0]*nb_runs
  nb_gacha_landing = [0]*nb_runs
  nb_currency_landing = [0]*nb_runs
  
  for i in progressbar(range(nb_runs)):
    results[i] = board.nb_dice_required(
      target_score,
      pos= pos,
      nb_wish= nb_wish,
      wish_usage_priority= wish_usage_priority,
    )
    nb_extra_die_landing[i] = board.nb_extra_die_landing
    nb_extra_wish_landing[i] = board.nb_extra_wish_landing
    nb_cat_landing[i] = board.nb_cat_landing
    nb_gacha_landing[i] = board.nb_gacha_landing
    nb_currency_landing[i] = board.nb_currency_landing
  
  print("-"*26)
  print(f"Priority set on: {WishUsagePriority.print(wish_usage_priority)}")
  
  print("-"*26)
  print(f"  Landed on  |  # (median)")
  print("-"*26)
  print(f"{'Gacha':^13}|{median(nb_gacha_landing):^7}")
  print(f"{'Extra Wish':^13}|{median(nb_extra_wish_landing):^7}")
  print(f"{'Extra Die':^13}|{median(nb_extra_die_landing):^7}")
  print(f"{'Cat':^13}|{median(nb_cat_landing):^7}")
  print(f"{'Currency':^13}|{median(nb_currency_landing):^7}")
  print("-"*26)
  
  rmin, rmax = min(results), max(results)
  rsum, rmed = sum(results), median(results)
  ravg, rmod = rsum/nb_runs, mode(results)
  print(f"Nb dice required to reach {target_score}:")
  print(f"min-max: {f'{rmin}-{rmax}':>6}  [{f'{rmin-nb_dice} to {rmax-nb_dice}':^6}]")
  print(f"average: {ravg:>6.2f}  [{fmt_dice_req(ravg-nb_dice,2):>6}]")
  print(f"median:  {rmed:>6.2f}  [{fmt_dice_req(rmed-nb_dice,1):>6}]")
  print(f"mode:    {rmod:>6.2f}  [{fmt_dice_req(rmod-nb_dice):>6}]")
  print("-"*26)


def run_simu_play_from_start(
  nb_runs: int,
  nb_starting_dice: int,
  nb_starting_wish: int,
  wish_usage_priority:int =WishUsagePriority.EXTRA_WISH,
  show_stats:bool =False,
):
  board = Board(nb_starting_dice, nb_starting_wish)
  lst_scores = [0] * nb_runs
  lst_used_dice = [0] * nb_runs
  if show_stats: print(f"{'score':^7}{'#dice':^7}")
  for i in progressbar(range(nb_runs)):
    board.reset()
    prev_pos = -1

    while board.dice + board.wish > 0:
      board.use_right_dice(wish_usage_priority)
    
    if show_stats:
      print(f"{board.score:^7}", end='')
      print(f"{board.nb_used_dice:^7}", flush=1)
    
    lst_scores[i] = board.score
    lst_used_dice[i] = board.nb_used_dice
  
  rmin, rmax = min(lst_scores), max(lst_scores)
  rsum, rmed = sum(lst_scores), median(lst_scores)
  ravg, rmod = rsum / nb_runs, mode(lst_scores)
  print(f"Score reached with {nb_starting_dice} ({board.nb_used_dice})"
        f" dice and {nb_starting_wish} ({board.nb_used_wish}) wish:")
  print(f"min-max: {f'{rmin}-{rmax}':>6}")
  print(f"average: {ravg:>6.2f}")
  print(f"median:  {rmed:>6.2f}")
  print(f"mode:    {rmod:>6.2f}")


class TaskType:
  NB_DICE_REQUIRED_TO_REACH_SCORE = 1
  SCORE_FROM_AVAILABLE_DICE = 2


if __name__ == "__main__":
  ...
  #TODO: console inputs to run simulations