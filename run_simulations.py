from ff_goose_game import *

if __name__ == "__main__":
  task_to_run = TaskType.NB_DICE_REQUIRED_TO_REACH_SCORE
  #task_to_run = TaskType.SCORE_FROM_AVAILABLE_DICE
  
  match task_to_run:
    case TaskType.NB_DICE_REQUIRED_TO_REACH_SCORE:
      run_simu_nb_dice_required(
        nb_runs= 2_000,
        currency_levels= [3,3,3], # 1, 2 or 3
        target_score= 80,
        pos= 16, #Heart 16 #Ara 
        nb_wish= 1, #Heart 3 #Ara 3
        #inventory + board_rewards + daily_rewards + quest*3 + daily selection (+ 4th quest)
        nb_dice= 15, #Heart 15 #Ara 5
        wish_usage_priority= WishUsagePriority.EXTRA_WISH
      )
      run_simu_nb_dice_required(
        nb_runs= 2_000,
        currency_levels= [3,3,3], # 1, 2 or 3
        target_score= 80,
        pos= 16, #Heart 16 #Ara 
        nb_wish= 1, #Heart 3 #Ara 3
        #inventory + board_rewards + daily_rewards + quest*3 + daily selection (+ 4th quest)
        nb_dice= 15, #Heart 15 #Ara 5
        wish_usage_priority= WishUsagePriority.GACHA
      )

    # WIP
    case TaskType.SCORE_FROM_AVAILABLE_DICE:
      run_simu_play_from_start(
        nb_runs= 1_000,
        nb_starting_dice= 50,
        nb_starting_wish= 1,
        show_stats= False
        #TODO: simulate daily progress by injecting dice/wish from:
        #   - board rewards
        #   - daily selection shop
        #   - natural quests progress
        #  depending if in "hoard mode" and not (fine tune thresholds)
      )