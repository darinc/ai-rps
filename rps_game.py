import random
from typing import List, Tuple

class Agent:
    def __init__(self, name: str, server: 'Server'):
        self.name = name
        self.server = server
        self.thought_history: List[str] = []
        self.last_result: str = ""
        self.last_scoreboard: str = ""
        self.opponent_moves: List[str] = []

    def make_move(self) -> str:
        self.think()
        self.maybe_chat()
        move = self.guess()
        return move

    def think(self) -> None:
        thought = f"{self.name} is analyzing previous moves and formulating a strategy..."
        if self.opponent_moves:
            thought += f" Opponent's last move was {self.opponent_moves[-1]}."
        self.thought_history.append(thought)

    def maybe_chat(self) -> None:
        if random.random() < 0.5:  # 50% chance to chat
            message = self.generate_chat_message()
            self.chat(message)

    def generate_chat_message(self) -> str:
        messages = [
            "I'm feeling lucky this round!",
            "You'll never guess what I'm going to play.",
            "Rock is looking pretty good right now...",
            "Scissors are sharp today.",
            "I heard paper is the way to go."
        ]
        return random.choice(messages)

    def chat(self, message: str) -> None:
        full_message = f"{self.name}: {message}"
        self.server.log_chat(full_message)

    def guess(self) -> str:
        choices = ["rock", "paper", "scissors"]
        if not self.opponent_moves:
            return random.choice(choices)
        
        # Simple strategy: counter the opponent's most frequent move
        counter_moves = {
            "rock": "paper",
            "paper": "scissors",
            "scissors": "rock"
        }
        opponent_favorite = max(set(self.opponent_moves), key=self.opponent_moves.count)
        return counter_moves[opponent_favorite]

    def update_results(self, result: Tuple[str, str]) -> None:
        winner, scoreboard = result
        self.last_result = winner
        self.last_scoreboard = scoreboard
        
        # Update opponent's last move
        if winner != "Tie":
            opponent_move = "rock"  # default
            if (winner == self.name and self.guess() == "paper") or (winner != self.name and self.guess() == "scissors"):
                opponent_move = "rock"
            elif (winner == self.name and self.guess() == "scissors") or (winner != self.name and self.guess() == "rock"):
                opponent_move = "paper"
            elif (winner == self.name and self.guess() == "rock") or (winner != self.name and self.guess() == "paper"):
                opponent_move = "scissors"
            self.opponent_moves.append(opponent_move)

class Server:
    def __init__(self):
        self.scoreboard = {
            "GPT-4o": 0,
            "Claude Sonnet 3.5": 0,
            "Ties": 0
        }
        self.chat_history: List[str] = []

    def process_round(self, agent1: Agent, move1: str, agent2: Agent, move2: str) -> Tuple[str, str]:
        print(f"{agent1.name} chose {move1}")
        print(f"{agent2.name} chose {move2}")
        
        if move1 == move2:
            winner = "Tie"
            self.scoreboard["Ties"] += 1
        elif (
            (move1 == "rock" and move2 == "scissors") or
            (move1 == "scissors" and move2 == "paper") or
            (move1 == "paper" and move2 == "rock")
        ):
            winner = agent1.name
            self.scoreboard[agent1.name] += 1
        else:
            winner = agent2.name
            self.scoreboard[agent2.name] += 1
        
        print(f"Winner: {winner}")
        return winner, self.get_scoreboard()

    def get_scoreboard(self) -> str:
        return f"Scoreboard: {self.scoreboard}"

    def log_chat(self, message: str) -> None:
        self.chat_history.append(message)

    def print_final_results(self) -> None:
        print("\nFinal Results:")
        print(self.get_scoreboard())
        print("\nChat History:")
        for message in self.chat_history:
            print(message)

def play_game(num_rounds: int = 10) -> None:
    server = Server()
    agent1 = Agent("GPT-4o", server)
    agent2 = Agent("Claude Sonnet 3.5", server)
    
    for round_num in range(1, num_rounds + 1):
        print(f"\nRound {round_num}")
        
        # Get moves from agents
        move1 = agent1.make_move()
        move2 = agent2.make_move()
        
        # Process round
        result = server.process_round(agent1, move1, agent2, move2)
        
        # Update agents with results
        agent1.update_results(result)
        agent2.update_results(result)
        
        # Log thought processes
        print("\nThought processes:")
        for thought in agent1.thought_history[-1:]:
            print(thought)
        for thought in agent2.thought_history[-1:]:
            print(thought)
    
    # Print final results
    server.print_final_results()
    
    print("\nFinal thought processes:")
    print(f"{agent1.name}:")
    for thought in agent1.thought_history:
        print(thought)
    print(f"\n{agent2.name}:")
    for thought in agent2.thought_history:
        print(thought)

if __name__ == "__main__":
    play_game()
