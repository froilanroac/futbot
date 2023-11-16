from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from database import database
import os

# menu admin
START_OVER, ADD_MEMBER, SHOW_REQUESTS, SELECTING_ACTION, SHOWING_MENU, SHOW_MEMBERS, OPEN_LIST, CLOSE_LIST, STOPPING, VALIDATING_CODE, GO_BACK_MENU, INVITATION_FOR_DELETE = range(12)
END = ConversationHandler.END

# adding member conversation
SELECTING_ROLE, SAVE_MEMBER, DECIDING_AFTER_ADDING_MEMBER = range(20,23)

admin_menu_keyboard = [
    ['Add member','Show members'],
    ['Show list', 'Close list', 'Open list'],
    ['Show invitations', 'Delete invitation'],
    ['/stop'],
]

admin_menu_markup = ReplyKeyboardMarkup(admin_menu_keyboard, one_time_keyboard=True)

# start 
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    '''Main menu for admin'''
    text = ("Main Menu, please select the opcions from the shorcuts. To abort, simply type /stop.")
    await update.message.reply_text(text=text, reply_markup=admin_menu_markup)
    return SELECTING_ACTION

async def stop_nested(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Stop conversation from within nested conversation.'''
    await update.message.reply_text("Bye admin!", reply_markup=ReplyKeyboardRemove())
    context.user_data['in_conversation'] = False
    return STOPPING

async def end_current_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Completely end conversation from within nested conversation.'''
    await update.message.reply_text("Ending current conversation, going back to menu...")
    await admin_menu(update, context)
    return GO_BACK_MENU

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''End Conversation by command.'''''
    await update.message.reply_text("Bye admin!", reply_markup=ReplyKeyboardRemove())
    context.user_data['in_conversation'] = False
    return ConversationHandler.END

async def show_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Show all requests and ask for a role'''
    requests = database.get_all_data('requests')
    # delete current keyboard
    await update.message.reply_text(text='Listing requests:', reply_markup=ReplyKeyboardRemove())
    if not requests:
        await update.message.reply_text('No requests, going back to menu')
        await admin_menu(update, context)
        return GO_BACK_MENU
    buttons = [ [InlineKeyboardButton(text=f"{request['name']}/{request['user_telegram_name']}/{request['telegram_user']}/{request['role']}", callback_data=str(request['id']))] for request in requests ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(text='Please Select a member to add from the list above', reply_markup=keyboard)
    return SELECTING_ROLE

async def select_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Get data from callback and ask for a role'''
    id = update.callback_query.data
    request = database.get_one('requests', id)
    context.user_data['add_member_request'] = request
    buttons = [ [InlineKeyboardButton(text=f"Resident", callback_data=str('resident'))], [InlineKeyboardButton(text=f"Exresident", callback_data=str('exresident'))] ]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        f"You want to add {request['name']} to the list, please tell me the role.",
        reply_markup=keyboard
    )
    return SAVE_MEMBER

async def save_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Save member in the list of his role'''
    role = update.callback_query.data
    request = context.user_data['add_member_request']
    request['role'] = role
    response = database.save_data('members', request)
    if response == 'Data saved successfully':
        response = database.delete_one('requests', request['id'])
        text = f"Member {request['name']} added successfully"
        createChatInviteLink = await update._bot.create_chat_invite_link(chat_id=os.getenv("CHAT_ID"), member_limit=1, expire_date=None)
        await update._bot.send_message(chat_id=request['id'], text=f"Bienvenido a la comunidad de Futbol Monteavila, este es el link de invitacion: {createChatInviteLink['invite_link']}")
    else:
        text = f"Error adding member {request['name']}"
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text)
    await update.effective_message.reply_text(text='Going back to menu...', reply_markup=admin_menu_markup)
    return GO_BACK_MENU
    
async def show_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''get all members and show them'''
    residents = [ f' {member["name"]} - {member["telegram_user"]}' for  member in database.get_all_data('members') if (member['role'] == 'resident')]
    exresidents = [ f' {member["name"]} - {member["telegram_user"]}' for  member in database.get_all_data('members') if (member['role'] == 'exresident')]
    await update.message.reply_text(text='Listing members:')
    await update.message.reply_text(text='Residents: \n' + '\n'.join(residents))
    await update.message.reply_text(text='Exresidents: \n' + '\n'.join(exresidents))
    await admin_menu(update, context)

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lista = database.get_all_data('list')
    text = 'Lista de futbol:' + '\n' + '\n'.join([f'{lista.index(member)+1}. {member["name"]} - {member["telegram_user"]}' for member in lista])
    await update.message.reply_text(text=text)
    await admin_menu(update, context)

async def open_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Open the list'''
    response = database.edit_list(True)
    await update.message.reply_text(text=response)
    await admin_menu(update, context)

async def close_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Close the list'''
    response = database.edit_list(False)
    await update.message.reply_text(text=response)
    await admin_menu(update, context)

async def clear_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Clean the list'''
    response = database.clear_list('list')
    await update.message.reply_text(text=response)
    await admin_menu(update, context)

async def clear_invitations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Clean the list'''
    response = database.clear_list('invitations')
    await update.message.reply_text(text=response)
    await admin_menu(update, context) 

async def show_invitations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''list all invitations'''
    invitations = database.get_all_data('invitations')
    text = 'Invitaciones:' + '\n' + '\n'.join([f'{member["name"]} - {member["id"]}' for member in invitations])
    await update.message.reply_text(text=text)
    await admin_menu(update, context)

async def show_invitations_for_deleting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''list all invitations'''
    invitations = database.get_all_data('invitations')
    text = 'Invitaciones:' + '\n' + '\n'.join([f'{member["name"]} - {member["id"]}' for member in invitations])
    await update.message.reply_text(text=text)
    await update.message.reply_text(text='Please type the NAME of the invitation you want to delete:')
    return INVITATION_FOR_DELETE

async def delete_invited(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = database.delete_one_by_name('invitations', update.message.text)
    await update.message.reply_text(text=response)
    await admin_menu(update, context)
    return SELECTING_ACTION

async def admin_ask_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Verify admin code'''
    if 'in_conversation' not in context.user_data.keys() or context.user_data['in_conversation'] == False:
        context.user_data['in_conversation'] = True
        await update.message.reply_text('Admin code:')
        return VALIDATING_CODE
    elif context.user_data['in_conversation'] == True:
        await update.message.reply_text('You are already in a conversation, please finish it first')
        return ConversationHandler.END

    
async def autenticate_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Verify admin code'''
    if update.message.text == os.getenv("ADMIN_CODE"):
        await admin_menu(update, context)
        return SELECTING_ACTION
    else:
        await update.message.reply_text('Wrong code, try again...')

async def wrong_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Wrong option'''
    await update.message.reply_text('Wrong option, try again...')

async def invalid_conversation_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Verify admin code'''
    await update.message.reply_text('Invalid option, going back to menu...')
    await admin_menu(update, context)
    return GO_BACK_MENU

async def time_out_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(text='Finishing conversation due to inactivity...')
    await stop(update, context)

# an specific admin conversation for adding members
add_member_conversation_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^Add member$"), show_requests)],
    states={
        SELECTING_ROLE: [ CallbackQueryHandler(select_role) ],
        SAVE_MEMBER: [ CallbackQueryHandler(save_member) ],
    },
    fallbacks=[CommandHandler("back", end_current_conversation), CommandHandler("stop", stop_nested), MessageHandler(filters.TEXT, invalid_conversation_option)],
    map_to_parent={
        STOPPING: END,
        GO_BACK_MENU: SELECTING_ACTION,
        END: SELECTING_ACTION
    }
)


# admin conversation handler
admin_selection_handler = [
    add_member_conversation_handler,
    MessageHandler(filters.Regex("^Show members$"), show_members),
    MessageHandler(filters.Regex("^Open list$"), open_list),
    MessageHandler(filters.Regex("^Close list$"), close_list),
    MessageHandler(filters.Regex("^Show list$"), show_list),
    MessageHandler(filters.Regex("^Show invitations$"), show_invitations),
    MessageHandler(filters.Regex("^Delete invitation$"), show_invitations_for_deleting),
    MessageHandler(filters.Regex("^Clear list$"), clear_list),
    MessageHandler(filters.Regex("^Clear invitations$"), clear_invitations),
    MessageHandler(filters.TEXT & ~filters.COMMAND, wrong_option)
]

admin_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start_admin", admin_ask_code)],
    states={
        VALIDATING_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, autenticate_admin)],
        SELECTING_ACTION: admin_selection_handler,
        INVITATION_FOR_DELETE : [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_invited)],
        ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, time_out_message)]
    },
    fallbacks=[CommandHandler("stop", stop), MessageHandler(filters.COMMAND, stop)],
    conversation_timeout=60
)
