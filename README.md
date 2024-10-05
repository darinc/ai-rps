# AI Rock Paper Scissors Game

This project implements an AI-powered Rock Paper Scissors game where two AI agents, GPT-4o and Claude Sonnet 3.5, play against each other. The game demonstrates how different AI models approach strategy in a simple game scenario.

## Features

- Two AI agents: GPT-4o (OpenAI) and Claude Sonnet 3.5 (Anthropic)
- Multiple rounds of Rock Paper Scissors
- AI-generated strategies and optional trash talk
- Logging of thought processes, chat messages, and game results
- JSON-based communication format

## Requirements

- Python 3.7+
- OpenAI API key
- Anthropic API key

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/ai-rock-paper-scissors.git
   cd ai-rock-paper-scissors
   ```

2. Install the required packages:
   ```
   pip install openai anthropic
   ```

3. Set up your API keys as environment variables:
   ```
   export OPENAI_API_KEY='your_openai_api_key_here'
   export ANTHROPIC_API_KEY='your_anthropic_api_key_here'
   ```

## Usage

Run the game with the default 10 rounds:

```
python rps_game.py
```

## How it Works

1. The game initializes two AI agents: GPT-4o and Claude Sonnet 3.5.
2. In each round:
   - Both agents are prompted to make a move (rock, paper, or scissors).
   - Agents provide their thoughts, optional chat messages, and moves in JSON format.
   - The server processes the round and determines the winner.
   - Results are logged and shared with the agents.
3. The game continues for the specified number of rounds.
4. Final results and statistics are displayed at the end.

## Output

The game generates several output files in a timestamped directory under the `log/` folder:

- `chat.log`: Contains all chat messages and round results.
- `gpt-4o-thought.log`: GPT-4o's thought processes for each round.
- `claude-sonnet-3.5-thought.log`: Claude Sonnet 3.5's thought processes for each round.

## Customization

You can modify the `num_rounds` parameter in the `play_game()` function call at the end of `rps_game.py` to change the number of rounds played.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
