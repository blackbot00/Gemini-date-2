from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.states import Registration
from utils.keyboards import get_main_menu
from database import db
from config import LOG_GROUP_1

router = Router()

# This triggers when a state button is clicked
@router.callback_query(Registration.state, F.data.startswith("regstate_"))
async def process_state(callback: types.CallbackQuery, state: FSMContext):
    selected_state = callback.data.split("_")[-1]
    await state.update_data(state=selected_state)
    
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(text="Male 👨", callback_data="gender_male"))
    kb.add(types.InlineKeyboardButton(text="Female 👩", callback_data="gender_female"))
    kb.add(types.InlineKeyboardButton(text="Other 🌈", callback_data="gender_other"))
    kb.adjust(2)
    
    await callback.message.edit_text(f"📍 State: {selected_state}\n\nStep 2: Select your Gender:", 
                                     reply_markup=kb.as_markup())
    await state.set_state(Registration.gender)

@router.callback_query(Registration.gender, F.data.startswith("gender_"))
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[-1]
    await state.update_data(gender=gender)
    
    builder = InlineKeyboardBuilder()
    for age in range(18, 46):
        builder.add(types.InlineKeyboardButton(text=str(age), callback_data=f"age_{age}"))
    builder.adjust(7)
    
    await callback.message.edit_text("Step 3: Select your Age:", reply_markup=builder.as_markup())
    await state.set_state(Registration.age)

@router.callback_query(Registration.age, F.data.startswith("age_"))
async def finish_reg(callback: types.CallbackQuery, state: FSMContext):
    age = callback.data.split("_")[-1]
    data = await state.get_data()
    
    user_doc = {
        "user_id": callback.from_user.id,
        "name": callback.from_user.first_name,
        "state": data['state'],
        "gender": data['gender'],
        "age": age,
        "is_premium": False,
        "daily_chats": 0,
        "status": "idle"
    }
    
    await db.users.update_one({"user_id": user_doc["user_id"]}, {"$set": user_doc}, upsert=True)
    await state.clear()
    
    # Log to Group 1
    await callback.bot.send_message(LOG_GROUP_1, f"✅ **New Registration**\n👤 {user_doc['name']}\n📍 {user_doc['state']}\n🧬 {user_doc['gender']}\n🎂 Age: {age}")
    
    await callback.message.edit_text(f"🎉 Welcome {user_doc['name']}! Registration complete.", 
                                     reply_markup=get_main_menu())
    
