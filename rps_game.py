import os
import random
from typing import List, Tuple
from openai import OpenAI
from anthropic import Anthropic
from datetime import datetime

class Agent:
    def __init__(self, name: str, server: 'Server'):
        self.name = name
        self.server = server
        self.thought_history: List[str] = []
        self.last_result: str = ""
        self.last_scoreboard: str = ""
        self.opponent_moves: List[str] = []
        self.log_file = os.path.join(server.log_directory, f"{name.lower().replace(' ', '-')}-thought.log")
        
        if self.name == "GPT-4o":
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            self.model = "gpt-4o-2024-08-06"
        elif self.name == "Claude Sonnet 3.5":
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = "claude-3-5-sonnet-20240620"

    def log_thought(self, round_num: int, thought: str):
        with open(self.log_file, 'a') as f:
            f.write(f"========= Round {round_num}:\n{thought}\n\n")

    def make_move(self) -> str:
        self.think()
        self.maybe_chat()
        return self.guess()

    def get_ai_response(self, prompt: str, max_tokens: int = 300) -> str:
        if self.name == "GPT-4o":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        elif self.name == "Claude Sonnet 3.5":
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text

    def review_and_update_guess(self, initial_guess: str, opponent_chat: str) -> str:
        prompt = f"You initially guessed {initial_guess} for this round of rock-paper-scissors. Your opponent then said: '{opponent_chat}'. Would you like to change your guess? If yes, what's your new guess? If no, stick with your original guess. Respond with only 'rock', 'paper', 'scissors', or 'stay'."
        decision = self.get_ai_response(prompt, max_tokens=10).lower().strip()
        return decision if decision in ["rock", "paper", "scissors"] else initial_guess

    def think(self) -> None:
        prompt = f"You are playing rock-paper-scissors. Your opponent's move history is {self.opponent_moves}. The current scoreboard is {self.last_scoreboard}. What's your strategy for the next move? Explain your reasoning."
        thought = self.get_ai_response(prompt)
        self.log_thought(len(self.thought_history) + 1, thought)
        self.thought_history.append(thought)

    def maybe_chat(self) -> None:
        if random.random() < 0.5:  # 50% chance to chat
            message = self.generate_chat_message()
            self.chat(message)

    def generate_chat_message(self) -> str:
        prompt = "Generate a short, strategic message to your opponent in a rock-paper-scissors game. Try to influence their next move or make them second-guess their strategy."
        return self.get_ai_response(prompt, max_tokens=100)

    def chat(self, message: str) -> None:
        full_message = f"{self.name}: {message}"
        self.server.log_chat(len(self.thought_history), full_message)

    def guess(self) -> str:
        prompt = f"Based on your previous analysis, what's your next move in rock-paper-scissors? Respond with only 'rock', 'paper', or 'scissors'."
        move = self.get_ai_response(prompt, max_tokens=10).lower().strip()
        return move if move in ["rock", "paper", "scissors"] else random.choice(["rock", "paper", "scissors"])

    def update_results(self, result: Tuple[str, str]) -> None:
        winner, scoreboard = result
        self.last_result = winner
        self.last_scoreboard = scoreboard
        
        if winner != "Tie":
            opponent_move = self.determine_opponent_move(winner)
            self.opponent_moves.append(opponent_move)

    def determine_opponent_move(self, winner: str) -> str:
        my_move = self.guess()
        if (winner == self.name and my_move == "paper") or (winner != self.name and my_move == "scissors"):
            return "rock"
        elif (winner == self.name and my_move == "scissors") or (winner != self.name and my_move == "rock"):
            return "paper"
        else:
            return "scissors"

class Server:
    def __init__(self):
        self.scoreboard = {
            "GPT-4o": 0,
            "Claude Sonnet 3.5": 0,
            "Ties": 0
        }
        self.chat_history: List[str] = []
        self.log_directory = self.create_log_directory()
        self.chat_log_file = os.path.join(self.log_directory, "chat.log")

    def create_log_directory(self) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        log_dir = os.path.join("log", timestamp)
        os.makedirs(log_dir, exist_ok=True)
        return log_dir

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
        
        # Log the round results
        round_num = len(agent1.thought_history)  # Assuming thought_history length represents the current round
        self.log_round_results(round_num, agent1, move1, agent2, move2, winner)
        
        return winner, self.get_scoreboard()

    def get_scoreboard(self) -> str:
        return f"Scoreboard: {self.scoreboard}"

    def log_chat(self, round_num: int, message: str) -> None:
        self.chat_history.append(message)
        with open(self.chat_log_file, 'a') as f:
            f.write(f"========= Round {round_num}: {message}\n")

    def log_round_results(self, round_num: int, agent1: Agent, move1: str, agent2: Agent, move2: str, winner: str):
        result_str = (
            f"Round {round_num} Results:\n"
            f"{agent1.name} chose: {move1}\n"
            f"{agent2.name} chose: {move2}\n"
            f"Winner: {winner}\n"
            f"{self.get_scoreboard()}\n"
        )
        with open(self.chat_log_file, 'a') as f:
            f.write(f"\n{result_str}\n")
        self.chat_history.append(result_str)

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
    agents = [agent1, agent2]
    
    last_winner = None

    for round_num in range(1, num_rounds + 1):
        print(f"\nRound {round_num}")
        
        try:
            # Determine the order of agents for this round
            if round_num == 1:
                random.shuffle(agents)
            elif last_winner:
                agents = [last_winner, agents[0] if agents[1] == last_winner else agents[1]]

            # Get initial moves from agents
            moves = [agent.make_move() for agent in agents]
            
            # Give the first agent a chance to review and update their guess
            if len(server.chat_history) > 0 and server.chat_history[-1].startswith(agents[1].name):
                moves[0] = agents[0].review_and_update_guess(moves[0], server.chat_history[-1].split(": ", 1)[1])

            # Process round
            result = server.process_round(agents[0], moves[0], agents[1], moves[1])
            
            # Update agents with results
            for agent in agents:
                agent.update_results(result)
            
            # Determine the winner for the next round
            last_winner = agents[0] if result[0] == agents[0].name else agents[1] if result[0] == agents[1].name else None
            
            # Log thought processes
            print("\nThought processes:")
            for agent in agents:
                print(f"{agent.name}: {agent.thought_history[-1]}")
            
            # Print chat history for this round
            print("\nChat history for this round:")
            for message in server.chat_history[-3:]:  # Show last 3 entries (2 possible chats + 1 round result)
                if not message.startswith("Round"):  # Don't print the round results here
                    print(message)
                    server.log_chat(round_num, message)
        
        except Exception as e:
            print(f"An error occurred in round {round_num}: {str(e)}")
            continue
    
    # Print final results
    server.print_final_results()
    
    print(f"\nFinal thought processes (saved in {server.log_directory}):")
    for agent in [agent1, agent2]:
        print(f"{agent.name}: ---------------------")
        for thought in agent.thought_history:
            print(thought)
        print()

if __name__ == "__main__":
    play_game()
