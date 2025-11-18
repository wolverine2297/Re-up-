        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("ℹ️ View Full How It Works Guide", callback_data="guide:0")],
            [InlineKeyboardButton("🆕 Start New Deal", callback_data="start_new_deal")],
            [InlineKeyboardButton("🛡️ Meet Our Verified Escrows", callback_data="show_escrows")],
        ])

    if query:
        try:
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
            return
        except Exception as e:
            logger.info(f"Couldn't edit message for main menu (fallback to send). Error: {e}")
            try:
                await query.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")
                return
            except Exception as e2:
                logger.error(f"Failed to send fallback main menu message: {e2}")
                return
    else:
        try:
            if update.effective_message:
                await update.effective_message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await context.bot.send_message(chat_id=user.id, text=text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send main menu: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        if update.effective_message:
            await update.effective_message.reply_text("❌ This bot only works in private chats. Please start a chat with me directly.")
        return

    user = update.effective_user
    save_user(user.username, user.id)

    if context.args:
        deal_id = context.args[0]
        if deal_id.startswith("ESC-"):
            deal = get_deal(deal_id)
            if deal and deal["status"] == "created":
                username = user.username
                updated = False
                if not deal.get("buyer_id") and deal.get("buyer_username", "").lstrip("@") == username:
                    deal["buyer_id"] = user.id
                    updated = True
                if not deal.get("seller_id") and deal.get("seller_username", "").lstrip("@") == username:
                    deal["seller_id"] = user.id
                    updated = True
                if updated:
                    save_deal(deal)
                    log_action(deal_id, "user_registered", "counterparty", user.id, f"username={username}")

                role = "SELLER" if deal.get("seller_id") == user.id else "BUYER"
                other_party = deal['buyer_username'] if role == "SELLER" else deal['seller_username']
                if update.effective_message:
                    await update.effective_message.reply_text(
                        f"🌟 <b>Escrow Invitation – {deal_id}</b>\n\n"
                        f"<b>Role:</b> {role}\n"
                        f"<b>From:</b> {other_party}\n"
                        f"<b>Item:</b> {deal['description']}\n"
                        f"<b>Amount:</b> {deal['original_amount']} via {deal['payment_method']}\n"
                        f"<b>Escrow:</b> @{deal['escrow_username']}\n\n"
                        f"This deal is secured by a verified professional. Funds are held until delivery is confirmed.\n\n"
                        f"✅ <b>Accept</b> to proceed, or <b>Decline</b> if you’re not interested.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("✅ Accept – I Agree to Terms", callback_data=f"accept:{deal_id}")],
                            [InlineKeyboardButton("❌ Decline – Not Interested", callback_data=f"decline:{deal_id}")],
                            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                        ]),
                        parse_mode="HTML"
                    )
                    return
    await show_main_menu(update, context)

# ==============================================================================
# 📚 GUIDE / ESCROW
# ==============================================================================

async def show_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    page = int((query.data.split(":")[1]) if query and query.data else (context.args[0] if context.args else 0))

    if page == 0:
        text = (
            "👤 <b>Who Can Use Castin Pro?</b>\n\n"
            "• <b>Buyers</b>: Pay securely knowing your money is held by a neutral, verified professional — never the seller.\n"
            "• <b>Sellers</b>: Deliver only after payment is 100% secured in escrow.\n"
            "• <b>Escrows</b>: Pre-vetted, trusted mediators with public track records and real payout addresses."
        )
        buttons = [
            [InlineKeyboardButton("➡️ Next: Deal Lifecycle", callback_data="guide:1")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
    elif page == 1:
        text = (
            "🔁 <b>Deal Lifecycle – Step by Step</b>\n\n"
            "1️⃣ <b>Create Deal</b> → 2️⃣ <b>Counterparty Accepts</b> → 3️⃣ <b>Buyer Pays Escrow</b>\n"
            "4️⃣ <b>Seller Delivers</b> → 5️⃣ <b>Buyer Confirms</b> → 6️⃣ <b>Funds Released</b>\n\n"
            "Every step is private, tracked with a unique <b>Deal ID</b> (e.g., <code>ESC-A7B3F9</code>), and secured by a verified Escrow."
        )
        buttons = [
            [InlineKeyboardButton("➡️ Next: Payment Methods", callback_data="guide:2")],
            [InlineKeyboardButton("🔙 Back to Roles", callback_data="guide:0")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
    else:
        text = (
            "💳 <b>Supported & Secure Payment Methods</b>\n\n"
            "We support the most reliable methods for global trading:\n\n"
            "• <b>PayPal</b> – Instant, buyer-protected\n"
            "• <b>Skrill</b> – Fast international e-wallet\n"
            "• <b>Crypto</b> – BNB (BEP20) or USDT (TRC20)\n"
            "• <b>ACH</b> – US bank transfer (USD only)\n"
            "• <b>Wire Transfer</b> – Global bank transfer\n\n"
            "🔒 <b>Your payment address is NEVER shown publicly.</b>\n"
            "It is revealed ONLY to you at the exact moment you need to pay."
        )
        buttons = [
            [InlineKeyboardButton("✅ Got It – Start a Deal", callback_data="start_new_deal")],
            [InlineKeyboardButton("🔙 Back to Flow", callback_data="guide:1")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]

    if query:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
    else:
        await show_main_menu(update, context)
        await context.bot.send_message(chat_id=update.effective_user.id, text=text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")

async def show_escrows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    text = (
        "🛡️ <b>Verified Escrow Agents</b>\n\n"
        "All Escrows are pre-approved professionals with public resolution rates:\n\n"
        "• <b>@Tradealer1✅</b> – 98% resolved, <1h average response\n"
        "• <b>@rixen10✅</b> – 95% resolved, <2h average response\n"
        "• <b>@Nolam11✅</b> – 97% resolved, <1h average response\n\n"
        "They hold funds securely and mediate disputes fairly. You can trust them with high-value trades."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🆕 Start New Deal", callback_data="start_new_deal")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ])
    if query:
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await context.bot.send_message(chat_id=update.effective_user.id, text=text, reply_markup=keyboard, parse_mode="HTML")

# ==============================================================================
# 🆕 DEAL CREATION FLOW
# ==============================================================================

async def start_new_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    user = query.from_user if query else update.effective_user
    save_user(user.username, user.id)

    can_create, msg = can_create_deal(user.id)
    if not can_create:
        if query:
            await query.message.reply_text(msg)
        else:
            await update.effective_message.reply_text(msg)
        return

    context.user_data.clear()
    context.user_data["step"] = "select_role"
    if query:
        # send new message to leave previous untouched
        await context.bot.send_message(
            chat_id=user.id,
            text="👤 <b>What is your role in this trade?</b>\n\nPlease select the option that matches your current transaction:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 I am the BUYER", callback_data="role:buyer")],
                [InlineKeyboardButton("💼 I am the SELLER", callback_data="role:seller")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]),
            parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=user.id,
            text="👤 <b>What is your role in this trade?</b>\n\nPlease select the option that matches your current transaction:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 I am the BUYER", callback_data="role:buyer")],
                [InlineKeyboardButton("💼 I am the SELLER", callback_data="role:seller")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]),
            parse_mode="HTML"
        )

# ==============================================================================
# 📝 TEXT INPUT HANDLER
# ==============================================================================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    user = update.effective_user
    save_user(user.username, user.id)

    text = update.message.text.strip()
    # FIRST: check if this user is expected to send a payout address (from AFTER buyer confirms)
    if user.id in PENDING_PAYOUT:
        # Pop the pending payout request
        deal_id, method = PENDING_PAYOUT.pop(user.id)
        address = text
        deal = get_deal(deal_id)
        if not deal:
            await update.message.reply_text("❌ Deal not found. Unable to save payout info.")
            return

        # Save seller payout details to deal
        try:
            deal["seller_payout_method"] = method
            deal["seller_payout_address"] = address
            save_deal(deal)
            log_action(deal_id, "seller_payout_provided", "seller", user.id, f"method={method} addr={address}")
        except Exception as e:
            logger.error(f"Failed to save seller payout for {deal_id}: {e}")
            await update.message.reply_text("❌ Failed to save payout information. Please try again.")
            return

        # Confirm to seller
        try:
            await update.message.reply_text(
                "✅ <b>Payout Details Saved</b>\n\n"
                "Your payout method and address have been recorded. The Escrow has been notified.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to confirm payout save to seller: {e}")

        # Notify escrow with the payout information and a Release button
        try:
            escrow_username = deal.get("escrow_username")
            escrow_id = ESCROW_IDS.get(escrow_username)
            if escrow_id:
                await context.bot.send_message(
                    chat_id=escrow_id,
                    text=(
                        f"🔔 <b>Payout Info for {deal_id}</b>\n\n"
                        f"Seller: @{deal.get('seller_username')}\n"
                        f"Payout Method: {deal.get('seller_payout_method')}\n"
                        f"Payout Address: <code>{deal.get('seller_payout_address')}</code>\n\n"
                        "When ready, release the funds to the seller below."
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔓 Release Funds to Seller", callback_data=f"escrow_release_funds:{deal_id}")],
                        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                    ]),
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Failed to notify escrow of payout info for {deal_id}: {e}")

        return  # we've processed the seller payout message

    # proceed with other text steps
    step = context.user_data.get("step")
    if not step:
        return

    if step == "enter_deal_link":
        match = re.search(r"(ESC-[A-Z0-9]{6,})", text, re.IGNORECASE)
        if not match:
            await update.message.reply_text(
                "❌ <b>Invalid or missing deal link</b>\n\n"
                "Please paste the exact deal link the buyer sent (e.g., https://t.me/CastinEscrow_bot?start=ESC-A1B2C3).",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]),
                parse_mode="HTML"
            )
            return

        deal_id = match.group(1).upper()
        deal = get_deal(deal_id)
        if not deal:
            await update.message.reply_text(
                f"❌ <b>Deal {deal_id} not found</b>\n\nPlease ask the buyer to ensure they created the deal and shared the correct link.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]),
                parse_mode="HTML"
            )
            return

        # Security: if a seller is already registered, do not allow link reuse
        current_username = user.username or ""
        intended_seller = (deal.get("seller_username") or "").lstrip("@")
        if deal.get("seller_id") and deal.get("seller_id") != user.id:
            # Already used by another seller
            await update.message.reply_text(
                "🔒 <b>Invite Link Already Used</b>\n\n"
                "This invite link has already been used to register a seller for this deal. "
                "If you believe this is an error, please contact the buyer directly.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]),
                parse_mode="HTML"
            )
            context.user_data.pop("step", None)
            return

        if intended_seller.lower() != current_username.lstrip("@").lower():
            await update.message.reply_text(
                "⚠️ <b>Seller mismatch</b>\n\n"
                "This deal appears to be for a different seller. If you believe this is an error, ask the buyer to verify the seller username in the deal or ask the buyer to re-create the deal with your @username.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]),
                parse_mode="HTML"
            )
            return

        updated = False
        if not deal.get("seller_id"):
            deal["seller_id"] = user.id
            updated = True
        if updated:
            save_deal(deal)
            log_action(deal_id, "seller_registered_via_link", "seller", user.id, f"username={current_username}")

        # Notify escrow of any seller payout info that might exist (usually none)
        seller_method = context.user_data.get("payment_method", "N/A")
        seller_payout = context.user_data.get("seller_payout_address", "N/A")
        try:
            escrow_username = deal.get("escrow_username")
            escrow_id = ESCROW_IDS.get(escrow_username)
            if escrow_id:
                await context.bot.send_message(
                    chat_id=escrow_id,
                    text=(
                        f"🔔 <b>Seller Registration – {deal_id}</b>\n\n"
                        f"Seller @{current_username} joined the deal.\n"
                        f"Payout Method: {seller_method}\n"
                        f"Payout Address: <code>{seller_payout}</code>"
                    ),
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Failed to notify escrow of seller registration for {deal_id}: {e}")

        # send the invitation to accept/decline as a NEW message (do not edit previous)
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=(
                    f"🌟 <b>Escrow Invitation – {deal_id}</b>\n\n"
                    f"<b>Role:</b> SELLER\n"
                    f"<b>From:</b> {deal.get('buyer_username')}\n"
                    f"<b>Item:</b> {deal.get('description')}\n"
                    f"<b>Amount:</b> {deal.get('original_amount')} via {deal.get('payment_method')}\n"
                    f"<b>Escrow:</b> @{deal.get('escrow_username')}\n\n"
                    f"✅ <b>Accept</b> to proceed, or <b>Decline</b> if you’re not interested."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Accept – I Agree to Terms", callback_data=f"accept:{deal_id}")],
                    [InlineKeyboardButton("❌ Decline – Not Interested", callback_data=f"decline:{deal_id}")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send invitation to seller via link: {e}")

        context.user_data.pop("step", None)
        return

    # Existing flows (counterparty, description, payment, amount, escrow selection, etc.)
    # ... (keep your original text-step handling untouched)
    # The following replicates the previous logic to avoid changes; only things added above or below are new.
    if step == "enter_counterparty":
        if not text.startswith("@"):
            await update.message.reply_text(
                "⚠️ <b>Invalid Username</b>\n\n"
                "Please enter a valid Telegram @username (e.g., @Alice).",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Role Selection", callback_data="role:buyer")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]),
                parse_mode="HTML"
            )
            return
        context.user_data["counterparty"] = text
        role = context.user_data.get("role", "")
        if role == "buyer":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Counterparty", callback_data="role:buyer")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ])
        else:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Continue", callback_data="next:desc")],
                [InlineKeyboardButton("🔙 Back to Counterparty", callback_data="role:buyer")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ])
        await update.message.reply_text(
            "📝 <b>Describe the Item</b>\n\n"
            "Please provide a detailed description of what you’re buying/selling:",
            reply_markup=kb,
            parse_mode="HTML"
        )
        context.user_data["step"] = "enter_description"
        return

    if step == "enter_description":
        context.user_data["description"] = text
        await update.message.reply_text(
            "💳 <b>Select Payment Method</b>\n\n"
            "Choose the payment method you’ll use:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 PayPal", callback_data="method:PayPal")],
                [InlineKeyboardButton("💸 Skrill", callback_data="method:Skrill")],
                [InlineKeyboardButton("🪙 Crypto (BNB/USDT)", callback_data="method:Crypto")],
                [InlineKeyboardButton("🏦 ACH (USD)", callback_data="method:ACH")],
                [InlineKeyboardButton("🌐 Wire Transfer", callback_data="method:Wire")],
                [InlineKeyboardButton("🔙 Back to Description", callback_data="next:counterparty")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]),
            parse_mode="HTML"
        )
        context.user_data["step"] = "select_payment"
        return

    if step == "enter_payout_address":
        context.user_data["seller_payout_address"] = text
        # Keep previous branching for buyer vs seller; but in our new flow, sellers won't reach this early
        if context.user_data.get("role") == "seller":
            await update.message.reply_text(
                "✅ <b>Payout Address Saved!</b>\n\n"
                "Now please paste the deal link the buyer sent (e.g., https://t.me/CastinEscrow_bot?start=ESC-A1B2C3).",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]),
                parse_mode="HTML"
            )
            context.user_data["step"] = "enter_deal_link"
            return

        role = context.user_data.get("role", "")
        if role == "buyer":
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Payout Address", callback_data="next:desc")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ])
        else:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Continue", callback_data="next:amount")],
                [InlineKeyboardButton("🔙 Back to Payout Address", callback_data="next:desc")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ])
        await update.message.reply_text(
            "💰 <b>Enter Amount</b>\n\n"
            "Enter the trade amount and currency (e.g., 200 USD or 0.005 BNB):",
            reply_markup=kb,
            parse_mode="HTML"
        )
        context.user_data["step"] = "enter_amount"
        return

    if step == "enter_amount":
        context.user_data["original_amount"] = text.strip()
        parts = text.strip().split()
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ <b>Invalid format</b>\n\nPlease enter amount and currency, e.g. `200 USD` or `0.005 BNB`.",
                parse_mode="HTML"
            )
            return

        amount_str = parts[0]
        currency = parts[1].upper()
        pm = context.user_data.get("payment_method", "")

        try:
            amount_float = float(amount_str)
        except Exception:
            await update.message.reply_text("❌ <b>Invalid amount</b>\n\nPlease enter a numeric amount (e.g., 200).", parse_mode="HTML")
            return

        valid = True
        err_msg = ""
        if pm == "Crypto":
            if currency not in ("BNB", "USDT"):
                valid = False
                err_msg = "For Crypto payments you must specify BNB or USDT as currency (e.g., `0.05 BNB` or `100 USDT`)."
        else:
            if currency not in ("USD", "$"):
                valid = False
                err_msg = "For PayPal / Skrill / ACH / Wire please specify the amount in USD (e.g., `200 USD`)."

        if not valid:
            await update.message.reply_text(f"❌ <b>Invalid payment/currency pairing</b>\n\n{err_msg}", parse_mode="HTML")
            return

        try:
            fee = amount_float * FEE_PERCENTAGE
            if currency in ("USD", "$"):
                total = amount_float + fee
                context.user_data["fee_amount"] = f"{fee:.2f} USD"
                context.user_data["total_with_fee"] = f"{total:.2f} USD"
            else:
                context.user_data["fee_amount"] = f"{fee:.8f} {currency}"
                context.user_data["total_with_fee"] = f"{amount_float + fee:.8f} {currency}"
        except Exception:
            context.user_data["fee_amount"] = "N/A"
            context.user_data["total_with_fee"] = text

        buttons = [InlineKeyboardButton(f"@{e}", callback_data=f"escrow:{e}") for e in VERIFIED_ESCROWS]
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        keyboard.append([InlineKeyboardButton("🔙 Back to Amount", callback_data="next:payout")])
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
        await update.message.reply_text(
            "🛡️ <b>Select a Verified Escrow</b>\n\n"
            "Choose an Escrow agent to oversee this deal:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        context.user_data["step"] = "select_escrow"
        return

# ==============================================================================
# 📎 PHOTO UPLOAD HANDLER
# ==============================================================================

AWAITING_PAYMENT_SCREENSHOT, AWAITING_DELIVERY_SCREENSHOT = range(2)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    user = update.effective_user
    save_user(user.username, user.id)

    deal_id_payment = context.user_data.get("awaiting_payment_screenshot_for")
    if deal_id_payment:
        deal = get_deal(deal_id_payment)
        if not deal:
            await update.message.reply_text("❌ Deal not found.")
            return

        await update.message.reply_text(
            "✅ <b>Payment Screenshot Received!</b>\n\n"
            "Escrow has been notified and will verify your payment shortly.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]),
            parse_mode="HTML"
        )

        escrow_username = deal["escrow_username"]
        escrow_id = ESCROW_IDS.get(escrow_username)
        if escrow_id:
            payment_method = deal.get("payment_method")
            original_amount = deal.get("original_amount")
            try:
                await context.bot.send_photo(
                    chat_id=escrow_id,
                    photo=update.message.photo[-1].file_id,
                    caption=(
                        f"🖼️ <b>Payment Screenshot Uploaded – {deal_id_payment}</b>\n\n"
                        f"@{deal['buyer_username']} has uploaded payment proof for {original_amount} via {payment_method}.\n\n"
                        f"Please confirm whether you received the payment."
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Confirm Received", callback_data=f"escrow_confirm_payment:{deal_id_payment}")],
                        [InlineKeyboardButton("❌ Not Received", callback_data=f"escrow_not_received:{deal_id_payment}")],
                        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                    ]),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to send payment screenshot to escrow: {e}")
        if "awaiting_payment_screenshot_for" in context.user_data:
            del context.user_data["awaiting_payment_screenshot_for"]
        return

    deal_id_delivery = context.user_data.get("awaiting_delivery_screenshot_for")
    if deal_id_delivery:
        deal = get_deal(deal_id_delivery)
        if not deal:
            await update.message.reply_text("❌ Deal not found.")
            return

        await update.message.reply_text(
            "✅ <b>Delivery Screenshot Received!</b>\n\n"
            "The buyer will be notified to confirm receipt.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            ]),
            parse_mode="HTML"
        )

        buyer_id = deal.get("buyer_id")
        if buyer_id:
            try:
                await context.bot.send_photo(
                    chat_id=buyer_id,
                    photo=update.message.photo[-1].file_id,
                    caption=(
                        f"📦 <b>Delivery Proof – Deal {deal_id_delivery}</b>\n\n"
                        f"The seller has uploaded proof of delivery. Please confirm if the item matches your expectations.\n\n"
                        f"Press ✅ Confirm Received if satisfied, or ❌ Reject - Not Satisfied to notify Escrow and Seller."
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Confirm Received", callback_data=f"buyer_confirm_delivery:{deal_id_delivery}")],
                        [InlineKeyboardButton("❌ Reject - Not Satisfied", callback_data=f"buyer_reject_delivery:{deal_id_delivery}")],
                        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                    ]),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to send delivery proof to buyer {buyer_id}: {e}")
        if "awaiting_delivery_screenshot_for" in context.user_data:
            del context.user_data["awaiting_delivery_screenshot_for"]
        return

    await update.message.reply_text("⚠️ I wasn't expecting a photo right now. Please follow the instructions for the current step.")

# ==============================================================================
# 🔘 CALLBACK HANDLER
# ==============================================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    data = query.data if query else None
    user = query.from_user if query else update.effective_user

    if data == "accept_terms":
        save_user(user.username, user.id)
        set_terms_accepted(user.id)
        await show_main_menu(update, context)
        return

    if data == "cancel_terms":
        if query:
            await query.edit_message_text("❌ You must accept the terms to use this bot. Goodbye.")
        else:
            await update.effective_message.reply_text("❌ You must accept the terms to use this bot. Goodbye.")
        return

    if data == "main_menu":
        await show_main_menu(update, context)
        return

    if data and data.startswith("guide:"):
        await show_guide(update, context)
        return

    if data == "show_escrows":
        await show_escrows(update, context)
        return

    if data == "start_new_deal":
        await start_new_deal(update, context)
        return

    # Role selection
    if data and data.startswith("role:"):
        role = data.split(":", 1)[1]
        context.user_data["role"] = role

        # ---------- CHANGE: Seller role no longer asked for payout method immediately ----------
        if role == "seller":
            # Set step to enter_deal_link and prompt seller to paste the deal link the buyer sent.
            context.user_data["step"] = "enter_deal_link"
            # Send a NEW message (do not edit the previous) so earlier screens remain visible.
            await context.bot.send_message(
                chat_id=user.id,
                text=(
                    "📎 <b>Seller — Paste Deal Link</b>\n\n"
                    "Please paste the deal link the buyer sent (e.g., https://t.me/CastinEscrow_bot?start=ESC-A1B2C3)."
                    "\n\n⚠️ Do NOT share your payout address now — you will be asked for payout details only after the buyer confirms delivery."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]),
                parse_mode="HTML"
            )
            return

        # Buyer default flow: ask for counterparty
        context.user_data["step"] = "enter_counterparty"
        if query:
            role_v = context.user_data.get("role", "")
            if role_v == "buyer":
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Role Selection", callback_data="start_new_deal")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ])
            else:
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Submit", callback_data="next:counterparty")],
                    [InlineKeyboardButton("🔙 Back to Role Selection", callback_data="start_new_deal")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ])
            # send new message leaving previous untouched
            await context.bot.send_message(chat_id=user.id, text="👤 <b>Enter Counterparty's Username</b>\n\nPlease enter the Telegram @username of the other party (e.g., @Bob):", reply_markup=kb, parse_mode="HTML")
        else:
            await context.bot.send_message(chat_id=user.id, text="👤 Enter Counterparty's Username. Please enter the Telegram @username of the other party (e.g., @Bob):", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Submit", callback_data="next:counterparty")]]), parse_mode="HTML")
        return

    # Navigation steps (kept)
    if data == "next:counterparty":
        context.user_data["step"] = "enter_counterparty"
        if query:
            role = context.user_data.get("role", "")
            if role == "buyer":
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Role Selection", callback_data="start_new_deal")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ])
            else:
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Submit", callback_data="next:counterparty")],
                    [InlineKeyboardButton("🔙 Back to Role Selection", callback_data="start_new_deal")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ])
            await context.bot.send_message(chat_id=user.id, text="👤 <b>Enter Counterparty's Username</b>\n\nPlease enter the Telegram @username of the other party (e.g., @Bob):", reply_markup=kb, parse_mode="HTML")
        return

    if data == "next:desc":
        context.user_data["step"] = "enter_description"
        if query:
            role = context.user_data.get("role", "")
            if role == "buyer":
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Counterparty", callback_data="next:counterparty")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ])
            else:
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Continue", callback_data="next:desc")],
                    [InlineKeyboardButton("🔙 Back to Counterparty", callback_data="next:counterparty")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ])
            await context.bot.send_message(chat_id=user.id, text="📝 <b>Describe the Item</b>\n\nPlease provide a detailed description of what you’re buying/selling:", reply_markup=kb, parse_mode="HTML")
        return

    # Payment method selection for buyers (unchanged behavior)
    if data and data.startswith("method:"):
        method = data.split(":", 1)[1]
        context.user_data["payment_method"] = method
        # If role was seller earlier, we used to ask for payout here; now we do not. Sellers will be asked AFTER buyer confirms delivery.
        context.user_data["step"] = "enter_amount"
        if query:
            role = context.user_data.get("role", "")
            if role == "buyer":
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Description", callback_data="next:desc")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ])
            else:
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Continue", callback_data="next:amount")],
                    [InlineKeyboardButton("🔙 Back to Description", callback_data="next:desc")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ])
            await context.bot.send_message(chat_id=user.id, text="💰 <b>Enter Amount</b>\n\nEnter the trade amount and currency (e.g., 200 USD or 0.005 BNB):", reply_markup=kb, parse_mode="HTML")
        return

    if data == "next:payout":
        context.user_data["step"] = "enter_payout_address"
        if query:
            role = context.user_data.get("role", "")
            if role == "buyer":
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Description", callback_data="next:desc")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ])
            else:
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Continue", callback_data="next:payout")],
                    [InlineKeyboardButton("🔙 Back to Description", callback_data="next:desc")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ])
            await context.bot.send_message(chat_id=user.id, text="📧 <b>Enter Payout Address</b>\n\nPlease provide your payment address for payout:", reply_markup=kb, parse_mode="HTML")
        return

    if data == "next:amount":
        context.user_data["step"] = "enter_amount"
        if query:
            role = context.user_data.get("role", "")
            if role == "buyer":
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Payout Address", callback_data="next:payout")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ])
            else:
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Continue", callback_data="next:amount")],
                    [InlineKeyboardButton("🔙 Back to Payout Address", callback_data="next:payout")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ])
            await context.bot.send_message(chat_id=user.id, text="💰 <b>Enter Amount</b>\n\nEnter the trade amount and currency (e.g., 200 USD or 0.005 BTC):", reply_markup=kb, parse_mode="HTML")
        return

    # Escrow selection / create deal
    if data and data.startswith("escrow:"):
        escrow = data.split(":", 1)[1]
        if escrow not in VERIFIED_ESCROWS:
            if query:
                await query.answer("❌ Invalid escrow selection.", show_alert=True)
            return

        deal_id = "ESC-" + str(uuid4())[:6].upper()
        deal = {
            "deal_id": deal_id,
            "status": "created",
            "escrow_username": escrow,
            "description": context.user_data.get("description", "N/A"),
            "original_amount": context.user_data.get("original_amount", "N/A"),
            "total_with_fee": context.user_data.get("total_with_fee", "N/A"),
            "payment_method": context.user_data.get("payment_method", "N/A"),
            "fee_amount": context.user_data.get("fee_amount", "N/A"),
        }

        creator_id = user.id
        creator_username = user.username or f"user{creator_id}"

        if context.user_data.get("role") == "buyer":
            deal.update({
                "buyer_id": creator_id,
                "buyer_username": creator_username,
                "seller_username": context.user_data.get("counterparty"),
            })
        else:
            deal.update({
                "seller_id": creator_id,
                "seller_username": creator_username,
                "buyer_username": context.user_data.get("counterparty"),
                # seller_payout fields intentionally left blank until payout stage
                "seller_payout_method": None,
                "seller_payout_address": None,
            })

        save_deal(deal)
        update_last_deal_creation(creator_id)
        log_action(deal_id, "deal_created", context.user_data.get("role", "unknown"), creator_id)

        try:
            escrow_username = deal.get("escrow_username")
            escrow_id = ESCROW_IDS.get(escrow_username)
            buyer_pm = context.user_data.get("payment_method", "N/A")
            buyer_amount = context.user_data.get("original_amount", "N/A")
            if escrow_id:
                await context.bot.send_message(
                    chat_id=escrow_id,
                    text=(
                        f"🔔 <b>New Deal {deal_id} — Buyer Payment Info</b>\n\n"
                        f"Buyer selected payment method: <b>{buyer_pm}</b>\n"
                        f"Declared amount: <b>{buyer_amount}</b>\n\n"
                        "If the buyer provided any account details, they will be forwarded when received."
                    ),
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Failed to notify escrow of buyer payment info for {deal_id}: {e}")

        link = f"https://t.me/{BOT_USERNAME}?start={deal_id}"
        if query:
            await context.bot.send_message(
                chat_id=user.id,
                text=(f"✅ <b>Deal {deal_id} Created Successfully!</b>\n\n"
                      f"🔗 <b>Share this secure link with {deal['seller_username'] if deal.get('buyer_id') else deal['buyer_username']}:</b>\n"
                      f"<code>{link}</code>\n\n"
                      f"They’ll see a one-tap acceptance screen. No setup needed.\n\n"
                      f"💡 <i>Tip: Send this link directly in Telegram for best results.</i>"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📌 Copy Link", callback_data=f"copy_link:{deal_id}")],
                    [InlineKeyboardButton("📤 Send to Counterparty", url=f"https://t.me/{(deal['seller_username'] or deal['buyer_username']).lstrip('@')}")],
                    [InlineKeyboardButton("🔙 View Deal Details", callback_data=f"view_deal:{deal_id}")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]),
                parse_mode="HTML"
            )
        else:
            await context.bot.send_message(
                chat_id=user.id,
                text=(f"✅ <b>Deal {deal_id} Created Successfully!</b>\n\n"
                      f"🔗 <b>Share this secure link with {deal['seller_username'] if deal.get('buyer_id') else deal['buyer_username']}:</b>\n"
                      f"<code>{link}</code>\n\n"
                      f"They’ll see a one-tap acceptance screen. No setup needed.\n\n"
                      f"💡 <i>Tip: Send this link directly in Telegram for best results.</i>"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📌 Copy Link", callback_data=f"copy_link:{deal_id}")],
                    [InlineKeyboardButton("📤 Send to Counterparty", url=f"https://t.me/{(deal['seller_username'] or deal['buyer_username']).lstrip('@')}")],
                    [InlineKeyboardButton("🔙 View Deal Details", callback_data=f"view_deal:{deal_id}")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]),
                parse_mode="HTML"
            )
        return

    # Deal acceptance/decline
    if data and (data.startswith("accept:") or data.startswith("decline:")):
        parts = data.split(":", 1)
        action = parts[0]
        deal_id = parts[1]
        deal = get_deal(deal_id)
        if not deal:
            if query:
                await query.edit_message_text("❌ Deal not found. It may have been cancelled or expired.")
            return

        if action == "accept":
            deal["status"] = "accepted"
            save_deal(deal)
            log_action(deal_id, "deal_accepted", "counterparty", user.id)

            other_id = deal.get("buyer_id") if deal.get("seller_id") == user.id else deal.get("seller_id")
            if other_id:
                if deal.get("buyer_id") == other_id:
                    payment_method = deal["payment_method"]
                    escrow_address = PAYMENT_ADDRESSES.get(payment_method, "Not available")
                    total_to_pay = deal["total_with_fee"]
                    original_amount = deal["original_amount"]
                    fee_amount = deal["fee_amount"]

                    await context.bot.send_message(
                        chat_id=other_id,
                        text=(
                            f"✅ <b>Counterparty Accepted Deal {deal_id}</b>\n\n"
                            f"The seller (@{deal['seller_username']}) has accepted your deal.\n\n"
                            f"👉 <b>Next Step: Send Payment to Escrow</b>\n\n"
                            f"💳 <b>Payment Method:</b> {payment_method}\n"
                            f"📧 <b>Escrow Address:</b> <code>{escrow_address}</code>\n"
                            f"🔖 <b>Reference:</b> {deal_id}\n\n"
                            f"💰 <b>Amount Breakdown:</b>\n"
                            f"• Original Amount: {original_amount}\n"
                            f"• Fee (5%): {fee_amount}\n"
                            f"• <b>Total to Pay: {total_to_pay}</b>\n\n"
                            f"⚠️ <i>Do NOT pay the seller directly. Funds must go to the Escrow only.</i>"
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("✅ I’ve Sent Payment", callback_data=f"payment_sent:{deal_id}")],
                            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                        ]),
                        parse_mode="HTML"
                    )
                else:
                    original_amount = deal["original_amount"]
                    await context.bot.send_message(
                        chat_id=other_id,
                        text=(
                            f"✅ <b>Deal {deal_id} Accepted</b>\n\n"
                            f"The buyer (@{deal['buyer_username']}) has accepted your deal.\n\n"
                            f"⏳ <b>Awaiting Payment</b>\n"
                            f"You’ll be notified when the buyer sends payment to the Escrow.\n\n"
                            f"💰 <b>Expected Amount:</b> {original_amount}\n"
                            f"(Plus fees collected separately)"
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 View Deal", callback_data=f"view_deal:{deal_id}")],
                            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                        ]),
                        parse_mode="HTML"
                    )

            escrow_username = deal.get("escrow_username")
            escrow_id = ESCROW_IDS.get(escrow_username)
            if escrow_id:
                original_amount = deal["original_amount"]
                payment_method = deal["payment_method"]
                await context.bot.send_message(
                    chat_id=escrow_id,
                    text=(
                        f"🛡️ <b>New Deal Assigned: {deal_id}</b>\n\n"
                        f"<b>Buyer:</b> @{deal['buyer_username']}\n"
                        f"<b>Seller:</b> @{deal['seller_username']}\n"
                        f"<b>Item:</b> {deal['description']}\n"
                        f"<b>Amount:</b> {original_amount} ({payment_method})\n"
                        f"<b>Total (inc. fees):</b> {deal['total_with_fee']}\n\n"
                        f"Wait for buyer to claim payment sent."
                    ),
                    parse_mode="HTML"
                )
            else:
                if query:
                    await query.message.reply_text(
                        f"⚠️ <b>Escrow Not Ready</b>\n\n"
                        f"Escrow @{deal['escrow_username']} hasn’t started this bot yet.\n"
                        f"Please ask them to send <code>/start</code> to @{BOT_USERNAME}.",
                        parse_mode="HTML"
                    )

            if query:
                await query.edit_message_text("✅ <b>Deal Accepted!</b>\n\nStatus: 🟡 Awaiting buyer payment.")
        else:
            deal["status"] = "declined"
            save_deal(deal)
            log_action(deal_id, "deal_declined", "counterparty", user.id)
            if query:
                await query.edit_message_text("❌ <b>Deal Declined</b>\n\nThe deal has been cancelled.")
        return

    # Payment actions
    if data and data.startswith("payment_sent:"):
        deal_id = data.split(":", 1)[1]
        deal = get_deal(deal_id)
        if not deal:
            if query:
                await query.edit_message_text("❌ Deal not found.")
            return

        if query:
            await query.edit_message_text(
                "✅ <b>Payment Claim Submitted!</b>\n\n"
                "The Escrow will confirm receipt shortly. You’ll be notified when payment is verified.\n\n"
                "Please <b>upload a screenshot</b> of your payment confirmation as proof.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🖼️ Upload Screenshot", callback_data=f"upload_payment_screenshot:{deal_id}")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]),
                parse_mode="HTML"
            )
        else:
            await context.bot.send_message(
                chat_id=user.id,
                text="✅ <b>Payment Claim Submitted!</b>\n\nThe Escrow will confirm receipt shortly. You’ll be notified when payment is verified.\n\nPlease <b>upload a screenshot</b> of your payment confirmation as proof.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🖼️ Upload Screenshot", callback_data=f"upload_payment_screenshot:{deal_id}")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]),
                parse_mode="HTML"
            )

        context.user_data["awaiting_payment_screenshot_for"] = deal_id
        return

    if data and data.startswith("upload_payment_screenshot:"):
        deal_id = data.split(":", 1)[1]
        if query:
            await query.edit_message_text(
                "📎 <b>Upload Payment Screenshot</b>\n\n"
                "Please send a screenshot of your payment confirmation now.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]),
                parse_mode="HTML"
            )
        else:
            await context.bot.send_message(chat_id=user.id, text="📎 <b>Upload Payment Screenshot</b>\n\nPlease send a screenshot of your payment confirmation now.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]), parse_mode="HTML")
        context.user_data["awaiting_payment_screenshot_for"] = deal_id
        return

    if data and (data.startswith("escrow_confirm_payment:") or data.startswith("escrow_not_received:")):
        parts = data.split(":", 1)
        action = parts[0]
        deal_id = parts[1]
        deal = get_deal(deal_id)
        if not deal:
            if query:
                await query.edit_message_text("❌ Deal not found.")
            return

        if action == "escrow_confirm_payment":
            deal["status"] = "payment_confirmed"
            deal["payment_confirmed_at"] = time.time()
            save_deal(deal)
            log_action(deal_id, "payment_confirmed", "escrow", user.id)

            if query:
                try:
                    await query.edit_message_text("✅ <b>Payment Confirmed!</b>\n\nNotifying seller to deliver the item.", parse_mode="HTML")
                except:
                    logger.info("Could not edit escrow's original notification message (maybe media).")

            seller_id = deal.get("seller_id")
            if seller_id:
                try:
                    await context.bot.send_message(
                        chat_id=seller_id,
                        text=(
                            f"✅ <b>Payment Secured – Deal {deal_id}</b>\n\n"
                            f"Amount: {deal['original_amount']} has been confirmed by the Escrow.\n\n"
                            f"Please deliver the item and upload proof of delivery."
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("📤 Upload Delivery Proof", callback_data=f"upload_delivery_proof:{deal_id}")],
                            [InlineKeyboardButton("✅ Mark Delivered", callback_data=f"seller_mark_delivered:{deal_id}")],
                            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                        ]),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify seller {seller_id} after escrow confirm: {e}")

            buyer_id = deal.get("buyer_id")
            if buyer_id:
                try:
                    await context.bot.send_message(
                        chat_id=buyer_id,
                        text=(
                            f"✅ <b>Payment Confirmed – Deal {deal_id}</b>\n\n"
                            f"Your payment has been confirmed by the Escrow.\n\n"
                            f"Awaiting seller to deliver the item."
                        ),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify buyer {buyer_id} after escrow confirm: {e}")

        else:
            if query:
                try:
                    await query.edit_message_text("❌ <b>Payment Not Received</b>\n\nInforming buyer.", parse_mode="HTML")
                except:
                    logger.info("Could not edit escrow 'not received' message (maybe media).")

            buyer_id = deal.get("buyer_id")
            if buyer_id:
                try:
                    await context.bot.send_message(
                        chat_id=buyer_id,
                        text=(
                            f"❌ <b>Payment Not Confirmed – Deal {deal_id}</b>\n\n"
                            f"The Escrow did not receive your payment.\n"
                            f"Please verify your transaction and contact the Escrow if needed."
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("📞 Contact Escrow", callback_data="contact_escrow")],
                            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                        ]),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify buyer {buyer_id} about payment not received: {e}")
        return

    # Seller indicates upload delivery proof or mark delivered
    if data and data.startswith("upload_delivery_proof:"):
        deal_id = data.split(":", 1)[1]
        if query:
            await query.edit_message_text(
                "📎 <b>Upload Delivery Proof</b>\n\n"
                "Please send a screenshot showing proof of delivery (e.g., buyer's confirmation message).",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]),
                parse_mode="HTML"
            )
        else:
            await context.bot.send_message(chat_id=user.id, text="📎 <b>Upload Delivery Proof</b>\n\nPlease send a screenshot showing proof of delivery.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]), parse_mode="HTML")
        context.user_data["awaiting_delivery_screenshot_for"] = deal_id
        return

    # BUYER confirms/rejects delivery
    if data and (data.startswith("buyer_confirm_delivery:") or data.startswith("buyer_reject_delivery:")):
        parts = data.split(":", 1)
        action = parts[0]
        deal_id = parts[1]
        deal = get_deal(deal_id)
        if not deal:
            if query:
                await query.edit_message_text("❌ Deal not found.")
            return

        if action == "buyer_confirm_delivery":
            try:
                deal["status"] = "delivery_confirmed"
                deal["delivery_confirmed_at"] = time.time()
                save_deal(deal)
                log_action(deal_id, "delivery_confirmed", "buyer", user.id)
            except Exception as e:
                logger.error(f"Failed to update deal on buyer confirm: {e}")

            # Acknowledge buyer with the exact requested message (send new message)
            buyer_notification = "Successfully confirmed the delivery — awaiting Escrow to release funds to the seller."
            try:
                # edit if possible
                if query:
                    try:
                        await query.edit_message_text(f"✅ <b>Delivery Confirmed</b>\n\n{buyer_notification}", parse_mode="HTML")
                    except:
                        # ignore edit failure
                        pass
                # Always send a fresh message to buyer as explicit confirmation
                await context.bot.send_message(chat_id=user.id, text=buyer_notification)
            except Exception as e:
                logger.error(f"Failed to notify buyer after confirm: {e}")

            # Notify seller that buyer confirmed and that escrow will process release
            seller_id = deal.get("seller_id")
            if seller_id:
                try:
                    await context.bot.send_message(
                        chat_id=seller_id,
                        text=(
                            f"✅ <b>Buyer Confirmed Receipt – Deal {deal_id}</b>\n\n"
                            f"The buyer has confirmed receipt of the item.\n"
                            f"The Escrow will now process the release of funds to your account."
                        ),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify seller {seller_id} after buyer confirm: {e}")

            # ASK SELLER for payout details NOW (Option 2: present method buttons, then ask for address)
            if seller_id:
                try:
                    # Ask for crypto payout method choices
                    await context.bot.send_message(
                        chat_id=seller_id,
                        text=(
                            f"💰 <b>Provide Payout Details – Deal {deal_id}</b>\n\n"
                            "Please select your payout method (choose one):"
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("BNB (BEP20)", callback_data=f"seller_payout_method:{deal_id}:BNB")],
                            [InlineKeyboardButton("USDT (TRC20)", callback_data=f"seller_payout_method:{deal_id}:USDT")],
                            [InlineKeyboardButton("BTC", callback_data=f"seller_payout_method:{deal_id}:BTC")],
                            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                        ]),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to ask seller for payout method for {deal_id}: {e}")

            # Notify Escrow with Release button
            escrow_username = deal.get("escrow_username")
            escrow_id = ESCROW_IDS.get(escrow_username)
            if escrow_id:
                try:
                    await context.bot.send_message(
                        chat_id=escrow_id,
                        text=(
                            f"✅ <b>Buyer Confirmed Delivery – Deal {deal_id}</b>\n\n"
                            f"The buyer has confirmed receipt of the item.\n\n"
                            f"Awaiting seller payout details (seller will be prompted). Please release funds when ready."
                        ),
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔓 Release Funds to Seller", callback_data=f"escrow_release_funds:{deal_id}")],
                            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                        ]),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify escrow {escrow_username} after buyer confirm: {e}")

            return

        else:
            # buyer rejected delivery
            try:
                deal["status"] = "delivery_disputed"
                save_deal(deal)
                log_action(deal_id, "delivery_rejected", "buyer", user.id)
            except Exception as e:
                logger.error(f"Failed to update deal on buyer reject: {e}")

            if query:
                try:
                    await query.edit_message_text(
                        "❌ <b>Delivery Rejected</b>\n\n"
                        "Thank you. We have notified the Seller and Escrow about your concern.",
                        parse_mode="HTML"
                    )
                except:
                    logger.info("Could not edit buyer message after reject (maybe media).")

            seller_id = deal.get("seller_id")
            if seller_id:
                try:
                    escrow_username = deal.get("escrow_username")
                    await context.bot.send_message(
                        chat_id=seller_id,
                        text=(
                            f"⚠️ <b>Buyer Rejected Delivery – Deal {deal_id}</b>\n\n"
                            f"The buyer has rejected the delivery.\n"
                            f"Please contact the Escrow <code>@{escrow_username}</code> to resolve this issue."
                        ),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify seller {seller_id} about buyer rejection: {e}")

            escrow_username = deal.get("escrow_username")
            escrow_id = ESCROW_IDS.get(escrow_username)
            if escrow_id:
                try:
                    await context.bot.send_message(
                        chat_id=escrow_id,
                        text=(
                            f"⚠️ <b>Buyer Rejected Delivery – Deal {deal_id}</b>\n\n"
                            f"The buyer has rejected the seller's delivery.\n"
                            f"Please contact both parties to mediate and resolve the dispute."
                        ),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify escrow {escrow_username} about buyer rejection: {e}")

            return

    # SELLER payout method callback (after buyer confirmed)
    if data and data.startswith("seller_payout_method:"):
        # Format: seller_payout_method:ESC-XXXXXX:METHOD
        parts = data.split(":", 2)
        if len(parts) < 3:
            if query:
                await query.answer("Invalid selection.", show_alert=True)
            return
        _, deal_id, method = parts
        deal = get_deal(deal_id)
        if not deal:
            if query:
                await query.edit_message_text("❌ Deal not found.")
            return

        seller_id = deal.get("seller_id")
        # Only allow the correct seller to respond (basic check)
        if seller_id and user.id != seller_id:
            await query.answer("You are not the seller for this deal.", show_alert=True)
            return

        # Record choice temporarily and ask seller to provide address via text
        PENDING_PAYOUT[user.id] = (deal_id, method)
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=(
                    f"📧 <b>Enter Your {method} Payout Address</b>\n\n"
                    f"Please provide your {method} payout address now (e.g., wallet address). "
                    "This will be shared only with the Escrow to release funds — not with the buyer."
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
                ]),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to prompt seller {user.id} for payout address for {deal_id}: {e}")
        return

    # Escrow release funds action
    if data and data.startswith("escrow_release_funds:"):
        deal_id = data.split(":", 1)[1]
        deal = get_deal(deal_id)
        if not deal:
            if query:
                await query.edit_message_text("❌ Deal not found.")
            return

        try:
            # Set deal as completed and maybe log release; For now just log & notify parties
            deal["status"] = "completed"
            save_deal(deal)
            log_action(deal_id, "funds_released", "escrow", user.id)

            # Notify seller and buyer
            seller_id = deal.get("seller_id")
            buyer_id = deal.get("buyer_id")
            if seller_id:
                await context.bot.send_message(chat_id=seller_id, text=f"🔓 <b>Funds Released – Deal {deal_id}</b>\n\nThe Escrow has released funds to your provided payout address.")
            if buyer_id:
                await context.bot.send_message(chat_id=buyer_id, text=f"🔔 <b>Funds Released – Deal {deal_id}</b>\n\nThe Escrow has released the funds to the seller. Thank you for using Castin Pro.")

            if query:
                await query.edit_message_text("✅ <b>Funds Released</b>\n\nYou have released funds to the seller.")
        except Exception as e:
            logger.error(f"Failed during escrow release: {e}")
            if query:
                await query.edit_message_text("❌ Failed to release funds. See logs.")
        return

    # Fallbacks for other callbacks (view_deal, copy_link, etc.) remain unchanged
    if data and data.startswith("view_deal:"):
        deal_id = data.split(":", 1)[1]
        deal = get_deal(deal_id)
        if not deal:
            if query:
                await query.edit_message_text("❌ Deal not found.")
            return
        text = (
            f"📄 <b>Deal {deal_id}</b>\n\n"
            f"<b>Buyer:</b> @{deal.get('buyer_username')}\n"
            f"<b>Seller:</b> @{deal.get('seller_username')}\n"
            f"<b>Escrow:</b> @{deal.get('escrow_username')}\n"
            f"<b>Amount:</b> {deal.get('original_amount')}\n"
            f"<b>Payment Method:</b> {deal.get('payment_method')}\n"
            f"<b>Status:</b> {deal.get('status')}\n"
        )
        if query:
            await query.message.reply_text(text, parse_mode="HTML")
        else:
            await context.bot.send_message(chat_id=user.id, text=text, parse_mode="HTML")
        return

    # any other callbacks fall back to a safe message
    if query:
        await query.answer()

# ==============================================================================
# 🚀 BOOT
# ==============================================================================

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_text))
    # (Other handlers you already had can be registered here if any.)

    logger.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
