"""
CrewAI Manager

This module manages the CrewAI system, coordinating agents and tasks
for the Pokemon ROM player.
"""

import os
import yaml
import time
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from crewai import Crew, Process, Task
from utils.logger import get_logger
from utils.config_manager import load_config

from .agents.crew_battle_agent import CrewBattleAgent
from .agents.crew_navigation_agent import CrewNavigationAgent
from .agents.crew_menu_agent import CrewMenuAgent

logger = get_logger("crew")

@dataclass
class TaskDependency:
    """Represents a task's dependencies and dependents."""
    dependencies: Set[str] = field(default_factory=set)  # Tasks this task depends on
    dependents: Set[str] = field(default_factory=set)    # Tasks that depend on this task

@dataclass
class TaskError:
    """Information about a task error."""
    task_name: str
    error: Exception
    attempt: int
    timestamp: float = field(default_factory=time.time)
    recovery_action: Optional[str] = None

@dataclass
class CrewConfig:
    """Configuration for the CrewAI system."""
    agent_config: Dict[str, Any] = field(default_factory=dict)
    task_config: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, config_dir: str) -> 'CrewConfig':
        """Load configuration from YAML files.
        
        Args:
            config_dir: Directory containing config files
            
        Returns:
            Loaded configuration
        """
        try:
            # Load agent config
            agent_path = os.path.join(config_dir, "agents.yaml")
            with open(agent_path, 'r') as f:
                agent_config = yaml.safe_load(f)
                
            # Load task config
            task_path = os.path.join(config_dir, "tasks.yaml")
            with open(task_path, 'r') as f:
                task_config = yaml.safe_load(f)
                
            return cls(
                agent_config=agent_config,
                task_config=task_config
            )
            
        except Exception as e:
            logger.error(f"Error loading crew config: {e}")
            return cls()

class CrewManager:
    """Manages the CrewAI system for Pokemon ROM player."""
    
    def __init__(self, config_dir: str = "src/crew/config"):
        """Initialize the crew manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        # Load configuration
        self.config = CrewConfig.from_yaml(config_dir)
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Initialize task tracking
        self.tasks: Dict[str, Task] = {}
        self.task_dependencies: Dict[str, TaskDependency] = {}
        self.completed_tasks: Set[str] = set()
        
        # Initialize error tracking
        self.task_errors: Dict[str, List[TaskError]] = {}
        self.consecutive_failures = 0
        self.error_config = self.config.task_config.get("error_handling", {})
        
        # Create crew
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=[],  # Tasks are added dynamically
            process=Process.sequential
        )
        
        logger.info("Initialized CrewManager")
        
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all CrewAI agents.
        
        Returns:
            Dictionary of initialized agents
        """
        agents = {}
        
        try:
            # Initialize battle agent
            battle_config = self.config.agent_config.get("battle_agent", {})
            agents["battle"] = CrewBattleAgent(
                name=battle_config.get("name", "CrewBattleAgent"),
                goal=battle_config.get("goal", "Execute optimal battle strategies"),
                backstory=battle_config.get("backstory", "Pokemon battle expert"),
                verbose=battle_config.get("verbose", True),
                llm_provider=battle_config.get("llm_provider", "openai")
            )
            
            # Initialize navigation agent
            nav_config = self.config.agent_config.get("navigation_agent", {})
            agents["navigation"] = CrewNavigationAgent(
                name=nav_config.get("name", "CrewNavigationAgent"),
                goal=nav_config.get("goal", "Navigate efficiently"),
                backstory=nav_config.get("backstory", "Expert pathfinder"),
                verbose=nav_config.get("verbose", True),
                mode=nav_config.get("mode", "explore")
            )
            
            # Initialize menu agent
            menu_config = self.config.agent_config.get("menu_agent", {})
            agents["menu"] = CrewMenuAgent(
                name=menu_config.get("name", "CrewMenuAgent"),
                goal=menu_config.get("goal", "Handle menu interactions"),
                backstory=menu_config.get("backstory", "Menu expert"),
                verbose=menu_config.get("verbose", True),
                llm_provider=menu_config.get("llm_provider", "openai")
            )
            
            return agents
            
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            return {}
            
    def _build_dependency_graph(self) -> None:
        """Build the task dependency graph from configuration."""
        try:
            dependencies = self.config.task_config.get("dependencies", {})
            
            # Initialize dependency tracking for all tasks
            for task_name in self.config.task_config:
                if task_name not in ["dependencies", "priorities", "error_handling"]:
                    self.task_dependencies[task_name] = TaskDependency()
                    
            # Add dependencies and dependents
            for task_name, deps in dependencies.items():
                for dep in deps:
                    # Add dependency
                    self.task_dependencies[task_name].dependencies.add(dep)
                    # Add dependent
                    self.task_dependencies[dep].dependents.add(task_name)
                    
        except Exception as e:
            logger.error(f"Error building dependency graph: {e}")
            
    def get_agent(self, agent_type: str) -> Optional[Any]:
        """Get an agent by type.
        
        Args:
            agent_type: Type of agent to get
            
        Returns:
            Agent instance if found, None otherwise
        """
        return self.agents.get(agent_type)
        
    def create_task(self, task_name: str, **kwargs) -> Optional[Task]:
        """Create a task from configuration.
        
        Args:
            task_name: Name of task to create
            **kwargs: Additional task parameters
            
        Returns:
            Created task if successful, None otherwise
        """
        try:
            task_config = self.config.task_config.get(task_name)
            if not task_config:
                logger.error(f"No configuration found for task: {task_name}")
                return None
                
            # Get agent for task
            agent_name = task_config.get("agent")
            agent = self.get_agent(agent_name)
            if not agent:
                logger.error(f"No agent found for task: {agent_name}")
                return None
                
            # Create task with config and overrides
            task_params = {
                **task_config.get("parameters", {}),
                **kwargs
            }
            
            task = Task(
                description=task_config["description"],
                agent=agent,
                expected_output=task_config["expected_output"],
                **task_params
            )
            
            # Store task
            self.tasks[task_name] = task
            return task
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return None
            
    def get_ready_tasks(self) -> List[str]:
        """Get list of tasks ready to execute (all dependencies satisfied).
        
        Returns:
            List of task names that are ready to execute
        """
        ready_tasks = []
        
        for task_name, deps in self.task_dependencies.items():
            if task_name not in self.completed_tasks:
                if deps.dependencies.issubset(self.completed_tasks):
                    ready_tasks.append(task_name)
                    
        return ready_tasks
        
    def handle_error(self, error: Exception, task_name: Optional[str] = None) -> bool:
        """Handle errors during crew execution.
        
        Args:
            error: The error that occurred
            task_name: Name of the task that failed (if applicable)
            
        Returns:
            True if error was handled successfully
        """
        try:
            logger.error(f"Crew error: {error}")
            
            # Get error recovery settings
            max_failures = self.error_config.get("max_consecutive_failures", 3)
            retry_delay = self.error_config.get("default_retry_delay", 1.0)
            recovery_actions = self.error_config.get("recovery_actions", {})
            
            # Track consecutive failures
            self.consecutive_failures += 1
            if self.consecutive_failures > max_failures:
                logger.error("Too many consecutive failures")
                return False
                
            # Record task error if applicable
            if task_name:
                if task_name not in self.task_errors:
                    self.task_errors[task_name] = []
                    
                # Get recovery action for this type of task
                recovery_action = None
                for error_type, action in recovery_actions.items():
                    if error_type in task_name.lower():
                        recovery_action = action
                        break
                        
                # Record error
                self.task_errors[task_name].append(TaskError(
                    task_name=task_name,
                    error=error,
                    attempt=len(self.task_errors[task_name]) + 1,
                    recovery_action=recovery_action
                ))
                
                # Try recovery action if available
                if recovery_action:
                    return self._execute_recovery_action(task_name, recovery_action)
                    
            # Default error recovery: wait and retry
            time.sleep(retry_delay)
            return True
            
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
            return False
            
    def _execute_recovery_action(self, task_name: str, action: str) -> bool:
        """Execute a recovery action for a failed task.
        
        Args:
            task_name: Name of the failed task
            action: Recovery action to execute
            
        Returns:
            True if recovery was successful
        """
        try:
            logger.info(f"Executing recovery action '{action}' for task {task_name}")
            
            if action == "retreat":
                # For battle failures, try to run from battle
                battle_agent = self.get_agent("battle")
                if battle_agent:
                    return battle_agent.execute_battle_turn(
                        screen_state={"action": "retreat"},
                        game_state={"in_battle": True}
                    )
                    
            elif action == "return_to_last_center":
                # For navigation failures, return to last Pokemon Center
                nav_agent = self.get_agent("navigation")
                if nav_agent:
                    nav_agent.clear_targets()
                    # TODO: Add logic to find and navigate to last Pokemon Center
                    return True
                    
            elif action == "reset_to_main":
                # For menu failures, try to return to main menu
                menu_agent = self.get_agent("menu")
                if menu_agent:
                    menu_agent.clear_requests()
                    menu_agent.add_request(MenuRequest(
                        action=MenuAction.CLOSE_MENU,
                        priority=100
                    ))
                    return True
                    
            logger.warning(f"Unknown recovery action: {action}")
            return False
            
        except Exception as e:
            logger.error(f"Error executing recovery action: {e}")
            return False
            
    def reset_error_state(self) -> None:
        """Reset error tracking state."""
        self.consecutive_failures = 0
        self.task_errors.clear()
        
    def get_task_errors(self, task_name: str) -> List[TaskError]:
        """Get list of errors for a specific task.
        
        Args:
            task_name: Name of the task
            
        Returns:
            List of task errors
        """
        return self.task_errors.get(task_name, [])
        
    def execute_task(self, task_name: str, **kwargs) -> Any:
        """Execute a task by name with error handling.
        
        Args:
            task_name: Name of task to execute
            **kwargs: Additional task parameters
            
        Returns:
            Task result
        """
        try:
            # Check if task is ready
            if not self.task_dependencies[task_name].dependencies.issubset(self.completed_tasks):
                logger.error(f"Task {task_name} has unmet dependencies")
                return None
                
            # Create task if needed
            task = self.tasks.get(task_name)
            if not task:
                task = self.create_task(task_name, **kwargs)
                if not task:
                    return None
                    
            # Execute task with retries
            max_retries = self.error_config.get("max_retries", 3)
            retry_delay = self.error_config.get("retry_delay", 1.0)
            
            for attempt in range(max_retries):
                try:
                    # Execute task
                    result = self.crew.execute_task(task)
                    
                    # Reset error state on success
                    self.reset_error_state()
                    
                    # Mark task as completed
                    self.completed_tasks.add(task_name)
                    
                    return result
                    
                except Exception as e:
                    logger.warning(f"Task {task_name} attempt {attempt + 1} failed: {e}")
                    if not self.handle_error(e, task_name):
                        return None
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        
            logger.error(f"All attempts to execute task {task_name} failed")
            return None
            
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            self.handle_error(e, task_name)
            return None
            
    def execute_all_tasks(self) -> bool:
        """Execute all tasks in dependency order.
        
        Returns:
            True if all tasks completed successfully
        """
        try:
            # Build dependency graph if needed
            if not self.task_dependencies:
                self._build_dependency_graph()
                
            # Execute tasks until all are completed
            while len(self.completed_tasks) < len(self.tasks):
                # Get ready tasks
                ready_tasks = self.get_ready_tasks()
                if not ready_tasks:
                    logger.error("No tasks ready to execute")
                    return False
                    
                # Execute each ready task
                for task_name in ready_tasks:
                    result = self.execute_task(task_name)
                    if result is None:
                        logger.error(f"Task {task_name} failed")
                        return False
                        
            return True
            
        except Exception as e:
            logger.error(f"Error executing tasks: {e}")
            return False 