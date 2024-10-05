import os
import random
import json
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
        response = self.get_ai_response_json()
        self.process_response(response)
        return response['guess']

    def get_ai_response(self, prompt: str, max_tokens: int = 300) -> str:
        print(f"\nDebug: Outgoing request for {self.name}")
        print(f"Prompt: {prompt}")
        print(f"Model: {self.model}")
        print(f"Max tokens: {max_tokens}")

        if self.name == "GPT-4o":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content
        elif self.name == "Claude Sonnet 3.5":
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            result = message.content[0].text

        print(f"\nDebug: Incoming response for {self.name}")
        print(f"Raw response: {result}")
        return result

    def get_ai_response_json(self) -> dict:
        prompt = self.create_prompt()
        response_str = self.get_ai_response(prompt)
        try:
            response = json.loads(response_str)
            print(f"\nDebug: Parsed JSON for {self.name}")
            print(f"Parsed response: {json.dumps(response, indent=2)}")
            self.thought_history.append(response)
            return response
        except json.JSONDecodeError as e:
            print(f"\nDebug: Error decoding JSON for {self.name}")
            print(f"Error message: {str(e)}")
            print(f"Response string: {response_str}")
            default_response = {"thoughts": "", "chat": "", "guess": random.choice(["rock", "paper", "scissors"])}
            print(f"Using default response: {json.dumps(default_response, indent=2)}")
            self.thought_history.append(default_response)
            return default_response

    def create_prompt(self) -> str:
        return f"""You are playing rock-paper-scissors. Your opponent's move history is {self.opponent_moves}. The current scoreboard is {self.last_scoreboard}.

Please provide your response in the following JSON format:

{{
    "thoughts": "Your strategy and reasoning for the next move",
    "chat": "A short, strategic message to your opponent (optional, leave empty string if you don't want to chat)",
    "guess": "Your move (rock, paper, or scissors)"
}}

Ensure your "guess" is exactly one of: "rock", "paper", or "scissors".
Your "thoughts" should explain your strategy.
Your "chat" is optional and should try to influence your opponent's next move or make them second-guess their strategy.

Respond with only the JSON object, no other text."""

    def process_response(self, response: dict) -> None:
        # Log thought
        thought = response.get('thoughts', '')
        self.log_thought(len(self.thought_history), thought)

        # Maybe chat
        chat_message = response.get('chat', '')
        if chat_message:
            self.chat(chat_message)

    def chat(self, message: str) -> None:
        full_message = f"{self.name}: {message}"
        self.server.log_chat(len(self.thought_history), full_message)

    def update_results(self, result: Tuple[str, str]) -> None:
        winner, scoreboard = result
        self.last_result = winner
        self.last_scoreboard = scoreboard
        
        if winner != "Tie":
            opponent_move = self.determine_opponent_move(winner)
            self.opponent_moves.append(opponent_move)

    def determine_opponent_move(self, winner: str) -> str:
        my_move = self.thought_history[-1]['guess']  # Get the last guess from thought history
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
            f.write(f"========= Round {round_num}:\n {message}\n")

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

            # Get moves from agents
            moves = [agent.make_move() for agent in agents]
            
            # Process round
            result = server.process_round(agents[0], moves[0], agents[1], moves[1])
            
            # Update agents with results
            for agent in agents:
                agent.update_results(result)
            
            # Determine the winner for the next round
            last_winner = agents[0] if result[0] == agents[0].name else agents[1] if result[0] == agents[1].name else None
            
            # Print thought processes
            print("\nThought processes:")
            for agent in agents:
                print(f"{agent.name}: {agent.thought_history[-1]['thoughts']}")
            
            # Print chat history for this round
            print("\nChat history for this round:")
            for message in server.chat_history[-3:]:  # Show last 3 entries (2 possible chats + 1 round result)
                if not message.startswith("Round"):  # Don't print the round results here
                    print(message)
        
        except Exception as e:
            print(f"An error occurred in round {round_num}: {str(e)}")
            continue
    
    # Print final results
    server.print_final_results()
    
    print(f"\nFinal thought processes (saved in {server.log_directory}):")
    for agent in [agent1, agent2]:
        print(f"{agent.name}: ---------------------")
        for thought in agent.thought_history:
            print(thought['thoughts'])
        print()

if __name__ == "__main__":
    play_game()
