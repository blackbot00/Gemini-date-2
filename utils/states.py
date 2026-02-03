from aiogram.fsm.state import State, StatesGroup

class Registration(StatesGroup):
    state = State()
    gender = State()
    age = State()

class ChatState(StatesGroup):
    searching = State()
    on_human_chat = State()
    on_ai_chat = State()
  
