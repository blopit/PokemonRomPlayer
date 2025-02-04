from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from utils.screenshot import take_screenshot, get_latest_screenshot
import os
import base64

# Set OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

def encode_image_to_base64(image_path):
    """Convert an image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_screenshot():
    """Take and analyze a screenshot of the game."""
    screenshot_path = take_screenshot()
    if not screenshot_path:
        return "Failed to capture screenshot"
    
    # Convert image to base64
    base64_image = encode_image_to_base64(screenshot_path)
    
    return {
        "screenshot_path": screenshot_path,
        "base64_image": base64_image
    }

# Create tools
screenshot_tool = Tool(
    name="Take Screenshot",
    func=analyze_screenshot,
    description="Take a screenshot of the Pokemon game and return its path and base64 encoding"
)

# Create LLM instances
vision_llm = ChatOpenAI(
    model="gpt-4-vision-preview-v2",
    max_tokens=1024,
    temperature=0.7
)

battle_llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7
)

# Create agents with different roles
screenshot_agent = Agent(
    role='Screenshot Analyzer',
    goal='Analyze game screenshots to determine the current game state',
    backstory='Expert at analyzing Pokemon game screenshots and determining the current state',
    llm=vision_llm,
    tools=[screenshot_tool],
    verbose=True
)

battle_agent = Agent(
    role='Battle Strategist',
    goal='Make optimal decisions during Pokemon battles',
    backstory='Expert Pokemon trainer with deep knowledge of battle mechanics and strategies',
    llm=battle_llm,
    verbose=True
)

# Create tasks for the agents
analyze_task = Task(
    description='Take a screenshot and analyze the current game state to determine if we are in a battle',
    expected_output='A detailed analysis of the current game state from the screenshot, including whether we are in battle',
    agent=screenshot_agent
)

battle_task = Task(
    description='If in battle, determine the best move to make based on the screenshot analysis',
    expected_output='A strategic decision on which move to use in the current battle situation',
    agent=battle_agent
)

# Create the crew
crew = Crew(
    agents=[screenshot_agent, battle_agent],
    tasks=[analyze_task, battle_task],
    verbose=True
)

# Execute the crew's tasks
result = crew.kickoff()
print("Crew execution result:", result) 
