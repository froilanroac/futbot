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
import datetime
from utils.variables import EXRESIDENTES_DIAS, LIMITE_LISTA, DIA_INVITADOS, HORA_INVITADOS, MAXIMO_INVITADOS

# states 
SELECTING_ACTION, REQUEST, WRITING_NAME, SELECTING_ROLE, STOPPING, TYPING_INVITED_NAME = range(6)
END = ConversationHandler.END

user_menu_keyboard = [
    ['Ver lista de futbol'],
    ['Agregame a la lista', 'Eliminame de la lista'],
    ['Agregar invitado'],
    ['Salir']

]
user_menu_markup = ReplyKeyboardMarkup(user_menu_keyboard, one_time_keyboard=True)

user_yes_no_keyboard = [
    ['Si','No'],
    ['Salir']
]
user_yes_no_markup = ReplyKeyboardMarkup(user_yes_no_keyboard, one_time_keyboard=True)

residente_exresidente_keyboard = [
    ['Residente','Exresidente']
]
residente_exresidente_markup = ReplyKeyboardMarkup(residente_exresidente_keyboard, one_time_keyboard=True)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Stop conversation'''
    await update.message.reply_text(text='Conversación finalizada', reply_markup=ReplyKeyboardRemove())
    context.user_data['in_conversation'] = False
    return ConversationHandler.END

async def stop_nested(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Stop conversation'''
    await update.message.reply_text(text='Conversación finalizada', reply_markup=ReplyKeyboardRemove())
    context.user_data['in_conversation'] = False
    return STOPPING

async def user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''User menu'''
    await update.message.reply_text(text='Menú de usuario, para salir, simplemente escriba /stop', reply_markup=user_menu_markup)
    return SELECTING_ACTION

async def autenticate_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Autenticate user'''
    if 'in_conversation' not in context.user_data.keys() or context.user_data['in_conversation'] == False:
        context.user_data['in_conversation'] = True
        user = database.get_one('members',update.message.from_user.id)
        if user:
            context.user_data['user_role'] = user['role']
            await update.message.reply_text(text='Usuario autenticado')
            await user_menu(update, context)
            return SELECTING_ACTION
        else:
            await update.message.reply_text(text='No estas registrado en el sistema. Si deseas registrarte, por favor escribe si, de lo contrario no.', reply_markup=user_yes_no_markup)
            return REQUEST
    elif context.user_data['in_conversation'] == True:
        await update.message.reply_text(text='Ya estas en una conversacion, por favor escribe /stop si deseas terminarla.')
        return ConversationHandler.END
    
    
async def ask_for_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Add user to list'''
    await update.message.reply_text(text='Para procesar tu solicitud, primero necesito tu *nombre y apellido*, se utilizara para validar tu relacion con la residencia.', parse_mode='Markdown',reply_markup=ReplyKeyboardRemove())
    return WRITING_NAME

async def ask_for_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Ask for role'''
    context.user_data['name'] = update.message.text
    await update.message.reply_text(text='Por favor, selecciona tu rol en la residencia:', reply_markup=residente_exresidente_markup)
    return SELECTING_ROLE

async def saving_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Saving member'''
    response = database.save_data('requests', {
        'id': update.message.from_user.id,
        'name': context.user_data['name'],
        'role': update.message.text,
        'telegram_user': update.message.from_user.username,
        'user_telegram_name': f'{update.message.from_user.first_name} {update.message.from_user.last_name}',
    })
    await update.message.reply_text(text='Soliciud registrada exitosamente, un administrador deberá procesarla, cuando asi sea, recibirás una invitacion al grupo.')
    await stop(update, context)
    return STOPPING
    
async def wrong_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Wrong option'''
    print(update.message.text)
    await update.message.reply_text('Opcion invalida, por favor selecciona una opcion del menu. Para salir, simplemente escribe /stop o Salir.')

async def add_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if database.get_list_state():
        lista = database.get_all_data('list')
        invitados = database.get_all_data('invitations')
        total_lista = len(lista) + len(invitados)
        if total_lista < LIMITE_LISTA:
            day_of_week = datetime.datetime.today().weekday()
            if context.user_data['user_role'] == 'exresident' and day_of_week not in EXRESIDENTES_DIAS:
                await update.message.reply_text(text='Lo siento, los exresidentes solo pueden agregarse a la lista a partir del dia martes...')
            else:
                user = database.get_one('list', update.message.from_user.id)
                if user:
                    await update.message.reply_text(text='Mano, ya estas en la lista...')
                else:
                    response = database.save_data('list', {
                        'id': update.message.from_user.id,
                        'name': f'{update.message.from_user.first_name} {update.message.from_user.last_name}',
                        'telegram_user': update.message.from_user.username,
                        'role': 'Residente' if context.user_data['user_role'] == 'resident' else 'Exresidente'
                    })
                    await update.message.reply_text(text='Agregado a la lista exitosamente.')
                    lista = database.get_all_data('list')
                    text = '*Lista actualizada*' + '\n' + '\n'.join([f'{member["name"]} - {member["role"]}' for member in lista])
                    text += '\n' + '\n'.join([f'{member["name"]} - {member["role"]}' for member in database.get_all_data('invitations')])
                    await update._bot.send_message(chat_id=os.getenv("CHAT_ID"), text=text, parse_mode='Markdown')
        else:
            await update.message.reply_text(text='La lista esta llena, se avisara por el grupo si algun cupo se libera.')
    else:
        await update.message.reply_text(text='La lista esta cerrada, se avisara por el grupo cuando este abierta nuevamente.')
    await user_menu(update, context)

async def remove_from_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = database.get_one('list', update.message.from_user.id)
    if user:
        response = database.delete_one('list', update.message.from_user.id)
        await update.message.reply_text(text='Eliminado de la lista exitosamente.')
        lista = database.get_all_data('list')
        text = '*Lista actualizada*' + '\n' + '\n'.join([f'{member["name"]} - {member["role"]}' for member in lista])
        text += '\n' + '\n'.join([f'{member["name"]} - {member["role"]}' for member in database.get_all_data('invitations')])
        await update._bot.send_message(chat_id=os.getenv("CHAT_ID"), text=text, parse_mode='Markdown')
    else:
        await update.message.reply_text(text='No estas en la lista.')
    await user_menu(update, context)

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    text = 'Lista: ' + '\n' + '\n'.join([f'{member["name"]} - {member["role"]}' for member in database.get_all_data('list')])
    text += '\n' + '\n'.join([f'{member["name"]} - {member["role"]}' for member in database.get_all_data('invitations')])
    await update.message.reply_text(text=text)
    await user_menu(update, context)

async def add_invited(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if database.get_list_state(): 
        if (datetime.datetime.today().weekday() == DIA_INVITADOS and datetime.datetime.now().hour >= HORA_INVITADOS) or datetime.datetime.today().weekday() == 4:
            total_lista = len(database.get_all_data('list')) + len(database.get_all_data('invitations'))
            if total_lista < LIMITE_LISTA:
                if database.count_user_invitations(update.message.from_user.id) < MAXIMO_INVITADOS:
                    await update.message.reply_text(text='Por favor, escribe el nombre y apellido de tu invitado.')
                    return TYPING_INVITED_NAME
                else:
                    await update.message.reply_text(text='Ya tienes el maximo de invitados permitidos.')
            else:
                await update.message.reply_text(text='La lista esta llena, se avisara por el grupo si algun cupo se libera.')
        else:
            await update.message.reply_text(text='Los invitados solo pueden ser agregados despues de las 8pm del dia jueves.')
    else:
        await update.message.reply_text(text='La lista esta cerrada, se avisara por el grupo cuando este abierta nuevamente.')
    await user_menu(update, context)

async def save_invited(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    '''Add invited'''
    response = database.save_data('invitations', {
        'id': update.message.from_user.id,
        'name': update.message.text,
        'role': 'Invitado'
    })
    await update.message.reply_text(text='Invitado agregado exitosamente.')
    text = '*Lista actualizada*' + '\n' + '\n'.join([f'{member["name"]} - {member["role"]}' for member in database.get_all_data('list')])
    text += '\n' + '\n'.join([f'{member["name"]} - {member["role"]}' for member in database.get_all_data('invitations')])
    await update._bot.send_message(chat_id=os.getenv("CHAT_ID"), text=text, parse_mode='Markdown')
    await user_menu(update, context)
    
    return SELECTING_ACTION


async def time_out_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(text='Por inactividad terminare la conversacion, por favor escribe /start si deseas comenzar de nuevo.')
    await stop(update, context)

user_request_conversation = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex(f'^Si$') | filters.Regex(f'^si$'), ask_for_name)],
    states={
        WRITING_NAME: [ MessageHandler(filters.TEXT & ~filters.COMMAND, ask_for_role)],
        SELECTING_ROLE: [ MessageHandler(filters.Regex(f'^Residente$') | filters.Regex(f'^Exresidente$'), saving_member)], 
    },
    fallbacks=[CommandHandler("stop", stop_nested), MessageHandler(filters.TEXT, wrong_option)],
    map_to_parent={
        END: SELECTING_ACTION,
        STOPPING: END,
        ConversationHandler.END: ConversationHandler.END
    },
)

user_request_handler = [
    user_request_conversation,
    MessageHandler(filters.Regex(f'^No$') | filters.Regex(f'^no$') | filters.Regex(f'^Salir$') | filters.Regex(f'^salir$'), stop),
    MessageHandler(filters.TEXT & ~filters.COMMAND, wrong_option)
]

user_selection_handler = [
    MessageHandler(filters.Regex(f'^Ver lista de futbol$'), show_list),
    MessageHandler(filters.Regex(f'^Agregame a la lista$'), add_to_list),
    MessageHandler(filters.Regex(f'^Eliminame de la lista$'), remove_from_list),
    MessageHandler(filters.Regex(f'^Agregar invitado$'), add_invited),
    MessageHandler(filters.Regex(f'^Salir$') | filters.Regex(f'^salir$'), stop),
    MessageHandler(filters.TEXT & ~filters.COMMAND, wrong_option)
]

user_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start", autenticate_user)],
    states={
        SELECTING_ACTION: user_selection_handler,
        REQUEST: user_request_handler,
        TYPING_INVITED_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_invited)],
        ConversationHandler.TIMEOUT: [MessageHandler(filters.ALL, time_out_message)]
    },
    fallbacks=[CommandHandler("stop", stop), MessageHandler(filters.COMMAND, stop)],
    conversation_timeout=60
)