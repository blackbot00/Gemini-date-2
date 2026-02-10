# --- 1. START COMMAND (Referral & Unlock Fix) ---
@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject):
    # Telegram ID-ah integer-ah eduthukuroam
    user_id = int(message.from_user.id)
    args = command.args
    
    # Database-la user irukaara-nu check
    user_exists = await db.users.find_one({"user_id": user_id})

    if args:
        # 🔓 UNLOCK LOGIC
        if "unlock_" in args:
            try:
                # String-ah irukura ID-ah integer-ah mathuroam
                target_id = int(args.split("_")[1])
                
                # Ippo number-ah compare pandrom
                if target_id == user_id:
                    expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
                    
                    # Force update (upsert)
                    result = await db.users.update_one(
                        {"user_id": user_id}, 
                        {"$set": {
                            "is_premium": True, 
                            "expiry_date": expiry.strftime("%Y-%m-%d %H:%M:%S")
                        }},
                        upsert=True
                    )
                    
                    if result.modified_count > 0 or result.upserted_id:
                        return await message.answer(
                            "✅ **Premium Activated!** 💎\n\n"
                            "Ads skip pannadhuku thanks! Ippo 1 hour-ku unlimited features use pannunga."
                        )
                    else:
                        print("DB Update failed but no error thrown.")
            except Exception as e:
                print(f"Unlock Error: {e}")

        # 👥 REFERRAL LOGIC
        elif "ref_" in args and not user_exists:
            try:
                referrer_id = int(args.split("_")[1])
                if referrer_id != user_id:
                    await db.users.update_one({"user_id": referrer_id}, {"$inc": {"ref_count": 1}})
                    referrer = await db.users.find_one({"user_id": referrer_id})
                    
                    if referrer and referrer.get("ref_count") >= 5 and not referrer.get("ref_reward_claimed"):
                        expiry = datetime.datetime.now() + datetime.timedelta(days=7)
                        await db.users.update_one({"user_id": referrer_id}, {
                            "$set": {
                                "is_premium": True, 
                                "expiry_date": expiry.strftime("%Y-%m-%d"), 
                                "ref_reward_claimed": True
                            }
                        })
                        try:
                            await message.bot.send_message(referrer_id, "🎉 5 Referrals Completed! **1 Week Premium** Activated! 💎")
                        except: pass
            except Exception as e:
                print(f"Referral Error: {e}")

    # Register user if not exists
    if not user_exists:
        await db.users.insert_one({
            "user_id": user_id,
            "name": message.from_user.full_name,
            "ref_count": 0,
            "is_premium": False,
            "joined_date": datetime.datetime.now().strftime("%Y-%m-%d")
        })

    await message.answer(f"✨ **Welcome {message.from_user.first_name}!** ❤️", reply_markup=get_main_menu())
                                                                                  
