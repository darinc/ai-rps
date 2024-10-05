import os
import random
from typing import List, Tuple
import openai
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

class Agent:
    def __init__(self, name: str, server: 'Server'):
        self.name = name
        self.server = server
        self.thought_history: List[str] = []
        self.last_result: str = ""
        self.last_scoreboard: str = ""
        self.opponent_moves: List[str] = []
        
        if self.name == "GPT-4o":
            openai.api_key = os.getenv("OPENAI_API_KEY")
        elif self.name == "Claude Sonnet 3.5":
            self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def make_move(self) -> str:
        self.think()
        self.maybe_chat()
        move = self.guess()
        return move

    def think(self) -> None:
        prompt = f"You are playing rock-paper-scissors. Your opponent's move history is {self.opponent_moves}. The current scoreboard is {self.last_scoreboard}. What's your strategy for the next move? Explain your reasoning."
        
        if self.name == "GPT-4o":
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            thought = response.choices[0].message.content
        elif self.name == "Claude Sonnet 3.5":
            response = self.anthropic.completions.create(
                model="claude-2",
                prompt=f"{HUMAN_PROMPT} {prompt}{AI_PROMPT}",
                max_tokens_to_sample=300
            )
            thought = response.completion

        self.thought_history.append(thought)

    def maybe_chat(self) -> None:
        if random.random() < 0.5:  # 50% chance to chat
            message = self.generate_chat_message()
            self.chat(message)

    def generate_chat_message(self) -> str:
        prompt = "Generate a short, strategic message to your opponent in a rock-paper-scissors game. Try to influence their next move or make them second-guess their strategy."
        
        if self.name == "GPT-4o":
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            message = response.choices[0].message.content
        elif self.name == "Claude Sonnet 3.5":
            response = self.anthropic.completions.create(
                model="claude-2",
                prompt=f"{HUMAN_PROMPT} {prompt}{AI_PROMPT}",
                max_tokens_to_sample=100
            )
            message = response.completion

        return message

    def chat(self, message: str) -> None:
        full_message = f"{self.name}: {message}"
        self.server.log_chat(full_message)

    def guess(self) -> str:
        prompt = f"Based on your previous analysis, what's your next move in rock-paper-scissors? Respond with only 'rock', 'paper', or 'scissors'."
        
        if self.name == "GPT-4o":
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            move = response.choices[0].message.content.lower().strip()
        elif self.name == "Claude Sonnet 3.5":
            response = self.anthropic.completions.create(
                model="claude-2",
                prompt=f"{HUMAN_PROMPT} {prompt}{AI_PROMPT}",
                max_tokens_to_sample=10
            )
            move = response.completion.lower().strip()

        # Ensure valid move
        if move not in ["rock", "paper", "scissors"]:
            move = random.choice(["rock", "paper", "scissors"])

        return move

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
        
        try:
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
                print(f"{agent1.name}: {thought}")
            for thought in agent2.thought_history[-1:]:
                print(f"{agent2.name}: {thought}")
            
            # Print chat history for this round
            print("\nChat history for this round:")
            for message in server.chat_history[-2:]:  # Assuming max 2 messages per round
                print(message)
        
        except Exception as e:
            print(f"An error occurred in round {round_num}: {str(e)}")
            continue
    
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
