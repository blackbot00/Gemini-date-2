from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from utils.states import Registration
from utils.keyboards import get_state_keyboard, get_main_menu
from database import db
from config import LOG_GROUP_1

router = Router()

@router.message(Registration.state)
async def process_state(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(state=callback.data.split("_")[-1])
    
    # Gender Keyboard
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Male 👨", callback_data="gender_male"),
         types.InlineKeyboardButton(text="Female 👩", callback_data="gender_female")],
        [types.InlineKeyboardButton(text="Transgender 🌈", callback_data="gender_trans")]
    ])
    await callback.message.edit_text("Step 2: Select your Gender:", reply_markup=kb)
    await state.set_state(Registration.gender)

@router.callback_query(F.data.startswith("gender_"))
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(gender=callback.data.split("_")[-1])
    
    # Age Keyboard (7 Columns as requested)
    builder = types.InlineKeyboardBuilder()
    for age in range(18, 46): # 18 to 45
        builder.add(types.InlineKeyboardButton(text=str(age), callback_data=f"age_{age}"))
    builder.adjust(7)
    
    await callback.message.edit_text("Step 3: Select your Age:", reply_markup=builder.as_markup())
    await state.set_state(Registration.age)

@router.callback_query(F.data.startswith("age_"))
async def finish_reg(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    age = callback.data.split("_")[-1]
    
    final_data = {
        "user_id": callback.from_user.id,
        "name": callback.from_user.first_name,
        "state": user_data['state'],
        "gender": user_data['gender'],
        "age": age,
        "is_premium": False,
        "daily_ai_limit": 40,
        "daily_human_limit": 11,
        "status": "idle"
    }
    
    await db.users.insert_one(final_data)
    await state.clear()
    
    # Registration Completed Log
    log_msg = f"✅ **New Registration**\n👤 Name: {final_data['name']}\n📍 State: {final_data['state']}\n🧬 Gender: {final_data['gender']}\n🎂 Age: {age}"
    await callback.bot.send_message(LOG_GROUP_1, log_msg)
    
    await callback.message.edit_text("🎉 Registration Completed!", reply_markup=get_main_menu())
  
