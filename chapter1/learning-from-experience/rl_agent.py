"""
Traditional Reinforcement Learning Agent using Q-learning.
This demonstrates the classical RL approach that requires extensive training.
"""

import numpy as np
import pickle
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import random
from game_environment import TreasureHuntGame


class QLearningAgent:
    """
    Q-learning agent for the treasure hunt game.
    Uses tabular Q-learning with state-action pairs.
    """
    
    def __init__(self, 
                 learning_rate: float = 0.2,
                 discount_factor: float = 0.99,
                 epsilon: float = 1.0,
                 epsilon_decay: float = 0.9995,
                 epsilon_min: float = 0.1):
        """
        Initialize Q-learning agent.
        
        Args:
            learning_rate: Alpha parameter for Q-value updates
            discount_factor: Gamma parameter for future rewards
            epsilon: Initial exploration rate
            epsilon_decay: Rate at which epsilon decreases
            epsilon_min: Minimum exploration rate
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        # Q-table: state_hash -> action -> Q-value
        self.q_table = defaultdict(lambda: defaultdict(float))
        
        # Statistics
        self.episode_rewards = []
        self.episode_lengths = []
        self.episode_victories = []  # Per-episode victory flag (1/0), for learning curves
        self.victories = 0
        self.total_episodes = 0
        self.learning_curve = []  # Snapshots recorded at checkpoints during train()

    def _get_state_hash(self, game: TreasureHuntGame) -> str:
        """
        Create a hashable representation of the game state.
        This is crucial for tabular Q-learning.
        """
        # Include relevant state information
        state_parts = [
            game.current_room.name,
            tuple(sorted([item.name for item in game.inventory])),
            tuple(sorted([item.name for item in game.current_room.items])),
            tuple(sorted(game.current_room.locked_exits.items())),
            game.current_room.has_guard and not game.current_room.guard_defeated
        ]
        
        return str(state_parts)
    
    def choose_action(self, game: TreasureHuntGame, training: bool = True) -> str:
        """
        Choose an action using epsilon-greedy strategy.
        """
        available_actions = game.get_available_actions()
        
        if not available_actions:
            return "look around"
        
        # Exploration vs exploitation
        if training and random.random() < self.epsilon:
            # Explore: choose random action
            return random.choice(available_actions)
        else:
            # Exploit: choose best action based on Q-values
            state_hash = self._get_state_hash(game)
            
            # Get Q-values for all available actions
            action_values = {
                action: self.q_table[state_hash][action] 
                for action in available_actions
            }
            
            # If all Q-values are 0 (unexplored), choose randomly
            if all(v == 0 for v in action_values.values()):
                return random.choice(available_actions)
            
            # Choose action with highest Q-value
            return max(action_values, key=action_values.get)
    
    def update_q_value(self, state: str, action: str, reward: float, 
                       next_state: str, next_actions: List[str], done: bool):
        """
        Update Q-value using the Q-learning update rule.
        Q(s,a) <- Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
        """
        current_q = self.q_table[state][action]
        
        if done:
            # Terminal state
            target = reward
        else:
            # Get maximum Q-value for next state
            if next_actions:
                max_next_q = max(
                    self.q_table[next_state][a] for a in next_actions
                )
            else:
                max_next_q = 0
            
            target = reward + self.discount_factor * max_next_q
        
        # Update Q-value
        self.q_table[state][action] = (
            current_q + self.learning_rate * (target - current_q)
        )
    
    def train_episode(self, game: TreasureHuntGame) -> Tuple[float, int, bool]:
        """
        Train the agent for one episode.
        
        Returns:
            Total reward, number of steps, victory status
        """
        game.reset()
        total_reward = 0
        steps = 0
        
        while not game.game_over:
            # Get current state
            state_hash = self._get_state_hash(game)
            
            # Choose action
            action = self.choose_action(game, training=True)
            
            # Execute action
            feedback, reward, done = game.execute_action(action)
            
            # Get next state
            next_state_hash = self._get_state_hash(game)
            next_actions = game.get_available_actions() if not done else []
            
            # Update Q-value
            self.update_q_value(
                state_hash, action, reward, 
                next_state_hash, next_actions, done
            )
            
            total_reward += reward
            steps += 1
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        # Update statistics
        self.episode_rewards.append(total_reward)
        self.episode_lengths.append(steps)
        self.episode_victories.append(1 if game.victory else 0)
        if game.victory:
            self.victories += 1
        self.total_episodes += 1

        return total_reward, steps, game.victory

    def train(self, num_episodes: int = 1000, verbose: bool = True,
              stochastic: bool = False, checkpoint_interval: int = 0) -> Dict[str, Any]:
        """
        Train the agent for multiple episodes.
        
        Args:
            num_episodes: Number of episodes to train
            verbose: Whether to print progress
            stochastic: Whether to use stochastic environment
            checkpoint_interval: If > 0, record a learning-curve snapshot
                (episode, windowed victory rate, Q-table size, epsilon) every
                this many episodes. Snapshots are stored in self.learning_curve.
        """
        game = TreasureHuntGame(stochastic=stochastic)
        
        # Adjust hyperparameters for stochastic environment
        if stochastic:
            # Slightly slower epsilon decay for stochastic environments
            original_decay = self.epsilon_decay
            self.epsilon_decay = min(0.9999, self.epsilon_decay * 1.001)
            if verbose:
                print(f"Adjusted epsilon_decay from {original_decay:.4f} to {self.epsilon_decay:.4f} for stochastic environment\n")
        
        window = checkpoint_interval if checkpoint_interval and checkpoint_interval > 0 else 1000

        for episode in range(num_episodes):
            reward, steps, victory = self.train_episode(game)

            # Record a learning-curve snapshot at each checkpoint
            if checkpoint_interval and checkpoint_interval > 0 and (episode + 1) % checkpoint_interval == 0:
                recent = self.episode_victories[-window:]
                self.learning_curve.append({
                    "episode": episode + 1,
                    "victory_rate": sum(recent) / len(recent) if recent else 0.0,
                    "q_table_size": len(self.q_table),
                    "epsilon": self.epsilon,
                })

            if verbose and (episode + 1) % 100 == 0:
                recent_rewards = self.episode_rewards[-100:]
                recent_victories = sum(
                    1 for r in recent_rewards if r > 50  # Approximate victory
                )
                avg_reward = np.mean(recent_rewards)
                
                print(f"Episode {episode + 1}/{num_episodes}")
                print(f"  Avg Reward (last 100): {avg_reward:.2f}")
                print(f"  Victories (last 100): {recent_victories}")
                print(f"  Epsilon: {self.epsilon:.3f}")
                print(f"  Q-table size: {len(self.q_table)}")
                print()
        
        return {
            "total_episodes": self.total_episodes,
            "total_victories": self.victories,
            "victory_rate": self.victories / self.total_episodes if self.total_episodes else 0.0,
            "final_epsilon": self.epsilon,
            "q_table_size": len(self.q_table),
            "episode_rewards": self.episode_rewards,
            "episode_lengths": self.episode_lengths,
            "learning_curve": self.learning_curve,
        }

    def evaluate(self, num_episodes: int = 100, verbose: bool = False, stochastic: bool = False) -> Dict[str, Any]:
        """
        Evaluate the trained agent without learning.
        
        Args:
            num_episodes: Number of episodes to evaluate
            verbose: Whether to print details
            stochastic: Whether to use stochastic environment
        """
        game = TreasureHuntGame(stochastic=stochastic)
        eval_rewards = []
        eval_lengths = []
        eval_victories = 0
        
        # Store original epsilon and set to 0 for evaluation
        original_epsilon = self.epsilon
        self.epsilon = 0
        
        for episode in range(num_episodes):
            game.reset()
            total_reward = 0
            steps = 0
            
            while not game.game_over:
                action = self.choose_action(game, training=False)
                feedback, reward, done = game.execute_action(action)
                total_reward += reward
                steps += 1
                
                if verbose and episode == 0:  # Show first evaluation episode
                    print(f"Step {steps}: {action}")
                    print(f"Feedback: {feedback}")
                    print()
            
            eval_rewards.append(total_reward)
            eval_lengths.append(steps)
            if game.victory:
                eval_victories += 1
        
        # Restore epsilon
        self.epsilon = original_epsilon
        
        return {
            "num_episodes": num_episodes,
            "victories": eval_victories,
            "victory_rate": eval_victories / num_episodes if num_episodes else 0.0,
            "avg_reward": np.mean(eval_rewards),
            "std_reward": np.std(eval_rewards),
            "avg_length": np.mean(eval_lengths),
            "std_length": np.std(eval_lengths)
        }
    
    def save(self, filepath: str):
        """Save the Q-table and parameters."""
        data = {
            "q_table": dict(self.q_table),
            "epsilon": self.epsilon,
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "statistics": {
                "total_episodes": self.total_episodes,
                "victories": self.victories,
                "episode_rewards": self.episode_rewards,
                "episode_lengths": self.episode_lengths
            }
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, filepath: str):
        """Load a saved Q-table and parameters."""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.q_table = defaultdict(lambda: defaultdict(float))
        for state, actions in data["q_table"].items():
            for action, value in actions.items():
                self.q_table[state][action] = value
        
        self.epsilon = data["epsilon"]
        self.learning_rate = data["learning_rate"]
        self.discount_factor = data["discount_factor"]
        
        stats = data.get("statistics", {})
        self.total_episodes = stats.get("total_episodes", 0)
        self.victories = stats.get("victories", 0)
        self.episode_rewards = stats.get("episode_rewards", [])
        self.episode_lengths = stats.get("episode_lengths", [])


class DQNAgent:
    """
    Deep Q-Network agent for comparison.
    Uses neural network function approximation instead of tabular Q-learning.
    """
    
    def __init__(self, 
                 state_dim: int = 128,
                 hidden_dim: int = 256,
                 learning_rate: float = 0.001,
                 discount_factor: float = 0.95,
                 epsilon: float = 1.0,
                 epsilon_decay: float = 0.995,
                 epsilon_min: float = 0.01,
                 batch_size: int = 32,
                 memory_size: int = 10000):
        """
        Initialize DQN agent with neural network.
        Note: Simplified implementation for demonstration.
        """
        self.state_dim = state_dim
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.batch_size = batch_size
        
        # Experience replay buffer
        self.memory = []
        self.memory_size = memory_size
        
        # Statistics
        self.episode_rewards = []
        self.episode_lengths = []
        self.victories = 0
        self.total_episodes = 0
        
        # Note: For full implementation, we would use PyTorch or TensorFlow
        # This is a simplified placeholder
        print("Note: DQN implementation requires neural network library.")
        print("Using simplified random policy for demonstration.")
    
    def choose_action(self, game: TreasureHuntGame, training: bool = True) -> str:
        """Choose action (simplified for demonstration)."""
        available_actions = game.get_available_actions()
        if not available_actions:
            return "look around"
        
        # Simplified: just use epsilon-greedy with random selection
        if training and random.random() < self.epsilon:
            return random.choice(available_actions)
        else:
            # In full implementation, this would use neural network
            return random.choice(available_actions)
    
    def train_episode(self, game: TreasureHuntGame) -> Tuple[float, int, bool]:
        """Train for one episode (simplified)."""
        game.reset()
        total_reward = 0
        steps = 0
        
        while not game.game_over:
            action = self.choose_action(game, training=True)
            feedback, reward, done = game.execute_action(action)
            total_reward += reward
            steps += 1
        
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        self.episode_rewards.append(total_reward)
        self.episode_lengths.append(steps)
        if game.victory:
            self.victories += 1
        self.total_episodes += 1
        
        return total_reward, steps, game.victory
